import boto3
from pdf2image import convert_from_path

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

def image_from_s3(key):
    image = bucket.Object(key)
    img_data = image.get().get('Body').read()

    print(f"img_data type: {type(img_data)}")
    # print(f"img_data: {img_data}")

def downloadFileFromS3(key,foldername):
    path = "./"+foldername+"/"+key;
    s3_client.download_file(BUCKET_NAME,key,path)
    print("File Downloaded")

def convertPdfToImage(filename,inputFolder,outputFolder):
    print("convertPdfToImage")
    images = convert_from_path("./"+inputFolder+"/"+filename+".pdf")
    print(f"image: {images}")
    for img in images:
        img.save('./'+outputFolder+'/'+filename+".jpg", 'JPEG')

def main():
    # Getting all objects from s3 bucket
    for obj in bucket.objects.all():
        # keyname (e.g = Xyz.pdf)
        keyname = obj.key
        print(f"obj: {obj}")
        # print(f"obj type: {keyname.split('.')[1]}")

        # filename (e.g = Xyz)
        filename = keyname.split(".")[0]
        isFileTypePdf = keyname.endswith(".pdf")

        print(f"filename: {filename}")
        print(f"filetype: {isFileTypePdf}")

        if isFileTypePdf:
            print("File is pdf")
            downloadFileFromS3(keyname, "temp_pdf")
            convertPdfToImage(filename,inputFolder="temp_pdf",outputFolder="temp_images")
        else:
            print("File is jpg/jpeg")


main()
