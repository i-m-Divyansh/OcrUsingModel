import boto3
import botocore.exceptions
from PIL import Image,ImageDraw
import re
from pdf2image import  convert_from_path
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import interpolation as inter


# S3 BUCKET CREDS

# FOR LOCAL FOLDERS
INPUT_PATH="temp_pdf"
OUTPUT_PATH="temp_images"
FINAL_PATH="output"

# AWS REKOGNITION
# Create a Rekognition client
rekognition = boto3.client('rekognition')

# S3 SESSION (FOR GETTING ALL DOCUMENTS NAME FROM S3)
session = boto3.Session(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)
s3 = session.resource("s3")
bucket = s3.Bucket(BUCKET_NAME)

# S3 CLIENT
s3_client = boto3.client(
    "s3",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)
s3 = boto3.resource('s3', region_name="ap-south-1")

# FOR CHECKING IF THE FOLDER IS EXIST OR NOT
def isFolderExist(path):
    isExist = os.path.exists(path)
    print(f"{path} folder exist!" if isExist == True else f"{path} folder does not exist!" )

    if not isExist:
        os.makedirs(path)
        print(f"{path} folder created!")

# TO UPLOAD FILE TO S3
def uploadFileToS3(folderName,filename,extension):
    try:
        # response = s3_client.upload_file(file_name, bucket, object_name)
        response = s3_client.upload_file(f"./{folderName}/{filename}_masked.{extension.lower()}", OUTPUT_BUCKET,filename+"_masked" + "."+extension.lower())
        print("File Uploaded")
        return True

        # print(f"response:{response}")

    except botocore.exceptions.ClientError as e:
        print("Something went wrong!")
        return False

# uploadFileToS3("./masked_pdf/21_masked.pdf","testPdf","PDF")


# FOR DOWNLOADING FILE FROM S3
def downloadFileFromS3(key,foldername):

    isFolderExist(foldername)

    path = "./"+foldername+"/"+key;
    s3_client.download_file(BUCKET_NAME,key,path)
    print("File Downloaded")

# FOR CONVERTING IMAGES TO PDF
def convertImagesToPdf(folderName,outputFolder,filename):
    isFolderExist(outputFolder)

    images = []
    for image in os.listdir(folderName):
        print(f"image:{image}")
        img = Image.open(f"./{folderName}/{image}")
        print(f"img:{img}")
        images.append(img)
        # deleteFile(folderName,image)

    print(f"images:{images}")
    convertedImages = []
    for img in images:
        img = img.convert("RGB")
        convertedImages.append(img)

    print(f"convertedImages:{convertedImages}")

    convertedImages[0].save(f"./{outputFolder}/{filename}_masked.pdf",save_all=True,append_images=convertedImages[1:])

# convertImagesToPdf("output","output")

# FOR CONVERTING PDF INTO IMAGES
def convertPdftoImages(inputPath,outputPath,fileName):
    pages = convert_from_path("./"+inputPath+f"/{fileName}.pdf")

    isFolderExist(outputPath)

    for i in range(len(pages)):
        pages[i].save('./'+outputPath+f'/{fileName}_'+ str(i) +'.jpg', 'JPEG')

def deleteFile(foldername,filename):
    os.remove(f"./{foldername}/{filename}")
    print(f"file with {filename} is deleted!")

def deleteFilesFromFolder(foldername):
    for image in os.listdir(foldername):
        os.remove(f"./{foldername}/{image}")


def detectTextFromImage(folderName,imageName):
    with open(f'./{folderName}/{imageName}', 'rb') as img:
        # Call the detect_labels function
        response = rekognition.detect_text(Image={'Bytes': img.read()})
        print(f"response:{response}")
        return response['TextDetections']

def maskImage(folerName,outputFolder,imageName,textDetections):

    image = Image.open(f"./{folerName}/{imageName}")
    regex = ("^[2-9]{1}[0-9]{3}\\" +
             "s[0-9]{4}\\s[0-9]{4}$")
    p = re.compile(regex)

    digits_boxes = []
    possible_UIDs = ""
    for text in textDetections:
        if text['Type'] == "LINE":
            # print(f"text:{text}")
            if (re.search(p, text['DetectedText'])):
                print(f"Searched Text:{text}")
                print(f'DetectedText:{text["DetectedText"]}')
                possible_UIDs = text["DetectedText"]
                digits_boxes.append(text["Geometry"]["BoundingBox"])
                digits = list(text['DetectedText'])

    print(f"digits_boxes:{digits_boxes}")
    # print(f"digits:{digits}")
    print(f"possible_UIDs:{possible_UIDs}")

    # for i, digit in enumerate(digits):
        # print(f"digit:{digit}")
        # print(f"i:{i}")

    # for UID in possible_UIDs:
    #     print(f"UID:{UID}")

    draw = ImageDraw.Draw(image)

    for box in digits_boxes:
        # print(f"box:{box}")
        # print(f"width:{image.width}")
        # print(f"height:{image.height}")
        # print(f"box[width]:{box['Width']}")
        # print(f"box[height]:{box['Height']}")

        # print(f"digits length:{len(digits)}")

        digit_w = box['Width'] / len(digits) * image.width * 4.5
        # digit_w = box['Width'] / len(digits)

        # print(f"digit_w:{digit_w}")

        xmin = int(box["Left"] * image.width)
        # Using Digit width
        # xmin = int(box["Left"] * image.width*digit_w)
        ymin = int(box["Top"] * image.height)
        # xmax = xmin + int(box["Width"] * image.width*0.95)
        # USING DIGIT WIDTH
        xmax = xmin + int(box["Width"] * image.width - digit_w)
        ymax = ymin + int(box["Height"] * image.height)

        # print(f"xmin:{xmin}")
        # print(f"ymin:{ymin}")
        # print(f"xmax:{xmax}")
        # print(f"ymax:{ymax}")
        #
        draw.rectangle((xmin, ymin, xmax, ymax), fill=(0, 0, 0))

    isFolderExist(outputFolder)
    # deleteFile(OUTPUT_PATH,imageName)
    image.save(f"./{outputFolder}/masked_{imageName}")


def DetectTextsFromImagesAndMask(folderName):
    for image in os.listdir(folderName):
        images = []
        print(f"img:{image}")
        images.append(image)
        TextDetections = detectTextFromImage(folderName,imageName=image)
        maskImage(folderName,outputFolder=FINAL_PATH,imageName=image,textDetections=TextDetections)
        # convertImagesToPdf(folderName,FINAL_PATH,filename=image)


    print(f"images:{images}")
    # imagesToPdf("output", images)


def find_score(arr, angle):
    data = inter.rotate(arr, angle, reshape=False, order=0)
    hist = np.sum(data, axis=1)
    score = np.sum((hist[1:] - hist[:-1]) ** 2)
    return hist, score


def skewCorrectionInFolder(foldername):
    for image in os.listdir(foldername):
        print(f"image:{image}")
        img = Image.open(f"./{foldername}/{image}")
        print(f"img:{img}")

        # convert to binary
        wd, ht = img.size
        pix = np.array(img.convert('1').getdata(), np.uint8)
        bin_img = 1 - (pix.reshape((ht, wd)) / 255.0)
        delta = 1
        limit = 5
        angles = np.arange(-limit, limit + delta, delta)
        scores = []
        for angle in angles:
            hist, score = find_score(bin_img, angle)
            scores.append(score)

        best_score = max(scores)
        best_angle = angles[scores.index(best_score)]

        # correct skew
        data = inter.rotate(bin_img, best_angle, reshape=False, order=0)
        img.save(f"./{foldername}/{image}")


skewCorrectionInFolder("temp_images")

def main():
    try:
        for obj in bucket.objects.all():
            print(f"obj:{obj}")
            # keyname (e.g = Xyz.pdf)
            keyname = obj.key
            print(f"keyname:{keyname}")
            # print(f"obj type: {keyname.split('.')[1]}")

            # filename (e.g = Xyz)
            filename = keyname.split(".")[0]
            isFileTypePdf = keyname.endswith(".pdf")

            print(f"filename: {filename}")
            print(f"isFileTypePdf: {isFileTypePdf}")

            if isFileTypePdf:
                print("File is pdf")
                downloadFileFromS3(keyname, INPUT_PATH)
                convertPdftoImages(inputPath=INPUT_PATH,outputPath=OUTPUT_PATH,fileName=filename)
                # PRE_PROCESSINGS
                skewCorrectionInFolder(OUTPUT_PATH)
                DetectTextsFromImagesAndMask(OUTPUT_PATH)
                # deleteFilesFromFolder(OUTPUT_PATH)
                convertImagesToPdf(FINAL_PATH,"masked_pdf",filename)
                # deleteFilesFromFolder(FINAL_PATH)
                uploadFileToS3("masked_pdf",filename,"PDF")
                # deleteFilesFromFolder("masked_pdf")

                # convertPdfToImage(filename,inputFolder="temp_pdf",outputFolder="temp_images")
            else:
                print("File is jpg/jpeg")

    except botocore.exceptions.ClientError as error:
        print(f"Something went wrong:{error}")


# main()