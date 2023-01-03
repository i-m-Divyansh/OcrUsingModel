import cv2
import numpy as np
import regex as re
from PIL import Image
import pytesseract
from ISR.models import RRDN
import os
import boto3
from pdf2image import convert_from_path
from botocore.exceptions import ClientError
import logging
import img2pdf


SR_Model = RRDN(weights='gans')
# pytesseract.pytesseract.tesseract_cmd = "/usr/share/tesseract-ocr"

# -----------------------------------------------------------------------

# Helper functions
def isFolderExist(path):
    isExist = os.path.exists(path)
    print(f"{path} folder exist!" if isExist == True else f"{path} folder does not exist!" )

    if not isExist:
        os.makedirs(path)
        print(f"{path} folder created!")


# isFolderExist("temp")

# -----------------------------------------------------------

multiplication_table = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0))

permutation_table = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8))


def compute_checksum(number):
    """Calculate the Verhoeff checksum over the provided number. The checksum
    is returned as an int. Valid numbers should have a checksum of 0."""

    # transform number list
    number = tuple(int(n) for n in reversed(str(number)))
    # print(number)

    # calculate checksum
    checksum = 0

    for i, n in enumerate(number):
        checksum = multiplication_table[checksum][permutation_table[i % 8][n]]

    # print(checksum)
    return checksum


def Regex_Search(bounding_boxes):
    possible_UIDs = []
    Result = ""

    for character in range(len(bounding_boxes)):
        if len(bounding_boxes[character]) != 0:
            Result += bounding_boxes[character][0]
        else:
            Result += '?'

    matches = [match.span() for match in re.finditer(r'\d{12}', Result, overlapped=True)]

    for match in matches:

        UID = int(Result[match[0]:match[1]])

        if compute_checksum(UID) == 0 and UID % 10000 != 1947:
            possible_UIDs.append([UID, match[0]])

    possible_UIDs = np.array(possible_UIDs)
    print(f"possible_UIDs:{possible_UIDs}")
    return possible_UIDs

def Mask_UIDs(image_path, possible_UIDs, bounding_boxes, rtype, SR=False, SR_Ratio=[1, 1]):
    img = cv2.imread(image_path)

    print(f"image_path: {image_path}")
    # inputPath = "./" + inputFolder + "/" + filename + ".pdf"
    file = image_path.split("/")[2]
    print(f"file:{file}")
    name = file.split(".")[0]
    print(f"name:{name}")


    if rtype == 2:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rtype == 3:
        img = cv2.rotate(img, cv2.ROTATE_180)
    elif rtype == 4:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    height = img.shape[0]

    if SR == True:
        height *= SR_Ratio[1]

    for UID in possible_UIDs:

        digit1 = bounding_boxes[UID[1]].split()
        digit8 = bounding_boxes[UID[1] + 7].split()

        h1 = min(height - int(digit1[4]), height - int(digit8[4]))
        h2 = max(height - int(digit1[2]), height - int(digit8[2]))

        if SR == False:
            top_left_corner = (int(digit1[1]), h1)
            bottom_right_corner = (int(digit8[3]), h2)
            botton_left_corner = (int(digit1[1]), h2 - 3)
            thickness = h1 - h2

        else:
            top_left_corner = (int(int(digit1[1]) / SR_Ratio[0]), int((h1) / SR_Ratio[1]))
            bottom_right_corner = (int(int(digit8[3]) / SR_Ratio[0]), int((h2) / SR_Ratio[1]))
            botton_left_corner = (int(int(digit1[1]) / SR_Ratio[0]), int((h2) / SR_Ratio[1] - 3))
            thickness = int((h1) / SR_Ratio[1]) - int((h2) / SR_Ratio[1])

        img = cv2.rectangle(img, top_left_corner, bottom_right_corner, (0, 0, 0), -1)

    if rtype == 2:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif rtype == 3:
        img = cv2.rotate(img, cv2.ROTATE_180)
    elif rtype == 4:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)


    # checking whether masked folder exist or not
    isFolderExist("masked")

    file_name = "./masked/"+image_path.split('/')[-1].split('.')[0] + "_masked" + "." + image_path.split('.')[-1]
    cv2.imwrite(file_name, img)
    # print(f'file_name: {file_name}')
    convertImageToPdf(filepath=file_name)
    uploadFileToS3(filepath=file_name,filename=name+"_masked")
    deleteFile(file_name)
    return file_name



def Extract_and_Mask_UIDs(image_path, SR=False, sr_image_path=None, SR_Ratio=[1, 1]):

    if SR == False:
        img = cv2.imread(image_path)
        # print(f"type: {type(img)}")
        # print(f"img: {img}")

    else:
        img = cv2.imread(sr_image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    rotations = [[gray, 1],
                 [cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE), 2],
                 [cv2.rotate(gray, cv2.ROTATE_180), 3],
                 [cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE), 4],
                 [cv2.GaussianBlur(gray, (5, 5), 0), 1],
                 [cv2.GaussianBlur(cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE), (5, 5), 0), 2],
                 [cv2.GaussianBlur(cv2.rotate(gray, cv2.ROTATE_180), (5, 5), 0), 3],
                 [cv2.GaussianBlur(cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE), (5, 5), 0), 4]]

    settings = ('-l eng --oem 3 --psm 11')

    for rotation in rotations:
        isFolderExist("temp");

        cv2.imwrite('./temp/rotated_grayscale.png', rotation[0])

        bounding_boxes = pytesseract.image_to_boxes(Image.open('./temp/rotated_grayscale.png'), config=settings).split(" 0\n")
        possible_UIDs = Regex_Search(bounding_boxes)

        if len(possible_UIDs) == 0:
            continue
        else:

            if SR == False:
                masked_img = Mask_UIDs(image_path, possible_UIDs, bounding_boxes, rotation[1])
            else:
                masked_img = Mask_UIDs(image_path, possible_UIDs, bounding_boxes, rotation[1], True, SR_Ratio)

            # print(possible_UIDs)
            return (masked_img, possible_UIDs)

    return (None, None)


# masked_img,possible_UIDs = Extract_and_Mask_UIDs("./Images/17.jpeg")

# print(possible_UIDs[0][0])

# -----------------------------------------------------------------------------------
ACCESS_KEY = "AKIAQ34Y5OZLLY47NDFW"
SECRET_KEY = "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"
BUCKET_NAME ="hdfctests"

session = boto3.Session(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)
s3 = session.resource("s3")
bucket = s3.Bucket(BUCKET_NAME)

s3_client = boto3.client(
    "s3",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)
s3 = boto3.resource('s3', region_name="ap-south-1")

def convertImageToPdf(filepath):
    print(f"filepath:{filepath}")
    image = Image.open(filepath)
    # print(f"image:{image}")

    pdf_bytes = img2pdf.convert(image.filename)

    # opening or creating pdf file
    file = open(filepath, "wb")

    # writing pdf files with chunks
    file.write(pdf_bytes)
    # print(f"written !!!")

    # closing image file
    image.close()

    # closing pdf file
    file.close()



def uploadFileToS3(filepath,filename):
    OutputBucketName = "hdfcoutput"

    try:
        # response = s3_client.upload_file(file_name, bucket, object_name)
        response = s3_client.upload_file(filepath, OutputBucketName,filename + ".pdf")
        print("File Uploaded")
        # print(f"response:{response}")

    except ClientError as e:
        print("Something went wrong!")
        logging.error(e)
        return False
    return True

# uploadFileToS3(filepath="./masked/One_masked.jpg",filename="Test")


def downloadFileFromS3(key, foldername):
    isFolderExist(foldername)
    path = "./" + foldername + "/" + key
    s3_client.download_file(BUCKET_NAME, key, path)
    print("File Downloaded")

def deleteFile(filepath):
    print(f"File Deleted!")
    if os.path.exists(filepath):
        print("")
        # os.remove(filepath)


def convertPdfToImage(filename, inputFolder, outputFolder):
    isFolderExist(inputFolder)
    isFolderExist(outputFolder)
    # print("convertPdfToImage")
    inputPath = "./" + inputFolder + "/" + filename + ".pdf"
    outputPath = './' + outputFolder + '/' + filename + ".jpg"
    images = convert_from_path(inputPath)
    print(f"image: {images}")
    for img in images:
        img.save(outputPath, 'JPEG')
    deleteFile(inputPath)


def maskAadhar8Digits(filename,folername):
    path = "./"+folername+"/"+filename

    print(f"path:{path}")
    Extract_and_Mask_UIDs(path)
    deleteFile(filepath=path)


def main():
    # Getting all objects from s3 bucket
    for obj in bucket.objects.all():
        # keyname (e.g = Xyz.pdf)
        keyname = obj.key
        # print(f"obj: {obj} , obj type {type(obj)}")

        # filename (e.g = Xyz)
        filename = keyname.split(".")[0]
        isFileTypePdf = keyname.endswith(".pdf")

        print(f"filename: {filename}")
        print(f"filetype: {isFileTypePdf}")

        if isFileTypePdf:
            print("File is pdf")
            downloadFileFromS3(keyname, "temp_pdf")
            convertPdfToImage(filename, inputFolder="temp_pdf", outputFolder="temp_images")
            maskAadhar8Digits(filename=filename+".jpg",folername="temp_images")
            # deleteFile(filepath="./temp_images/"+filename+".jpg")
        else:
            print("File is jpg/jpeg")
            downloadFileFromS3(keyname, "temp_images")
            maskAadhar8Digits(filename=filename+".jpg",folername="temp_images")
            # deleteFile(filepath="./temp_images/"+filename+".jpg")

# main()

import schedule
# from final import main
import time

# schedule.every(1).day.do(call_cronjob)
# schedule.every().hour.do(job)
schedule.every().day.at("19:10").do(main)
# schedule.every().monday.do(job)
# schedule.every().wednesday.at("13:15").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)