import PyPDF2
from PIL import Image
from pdf2image import convert_from_path

# with open("./pdf/avishek.pdf","rb") as file:
#     pdf = PyPDF2.PdfFileReader(file)
#
#     print(f"pdf:{pdf}")
#
#     print(f"pdf pages:{pdf.getNumPages()}")
#
#     for page in range(pdf.getNumPages()):
#     #     # Extract the page
#         pdf_page = pdf.getPage(page)
#
#         print(f"pdf_page:{pdf_page}")
#     #
#     #     # Use PIL to convert the page to an image
#         image = Image.frombytes('RGB', pdf_page.mediaBox.upperRight, pdf_page.extractText())
    #
    #     print(f"image:{image}")


# pages = convert_from_path("./pdf/avishek.pdf")
#
# for i in range(len(pages)):
#     pages[i].save('./pdfToImages/page_'+ str(i) +'.jpg', 'JPEG')

import boto3
import re
from PIL import Image,ImageDraw

image = Image.open("./pdfToImages/page_1.jpg")

# Create a Rekognition client
rekognition = boto3.client('rekognition')

# Open the image file
with open('./pdfToImages/page_1.jpg', 'rb') as img:
    # Call the detect_labels function
    response = rekognition.detect_text(Image={'Bytes': img.read()})

print(f"response:{response}")

textDetections = response['TextDetections']

regex = ("^[2-9]{1}[0-9]{3}\\" +
             "s[0-9]{4}\\s[0-9]{4}$")
p = re.compile(regex)

digits_boxes = []
possible_UIDs ="";
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
print(f"digits:{digits}")
print(f"possible_UIDs:{possible_UIDs}")

for i, digit in enumerate(digits):
    print(f"digit:{digit}")
    print(f"i:{i}")

for UID in possible_UIDs:
    print(f"UID:{UID}")

draw = ImageDraw.Draw(image)

for box in digits_boxes:
    print(f"box:{box}")
    print(f"width:{image.width}")
    print(f"height:{image.height}")
    print(f"box[width]:{box['Width']}")
    print(f"box[height]:{box['Height']}")

    print(f"digits length:{len(digits)}")

    digit_w = box['Width'] / len(digits)*image.width*4.5
    # digit_w = box['Width'] / len(digits)


    print(f"digit_w:{digit_w}")

    xmin = int(box["Left"] * image.width)
    # Using Digit width
    # xmin = int(box["Left"] * image.width*digit_w)
    ymin = int(box["Top"] * image.height)
    # xmax = xmin + int(box["Width"] * image.width*0.95)
    # USING DIGIT WIDTH
    xmax = xmin + int(box["Width"] * image.width-digit_w)
    ymax = ymin + int(box["Height"] * image.height)

    print(f"xmin:{xmin}")
    print(f"ymin:{ymin}")
    print(f"xmax:{xmax}")
    print(f"ymax:{ymax}")
#
    draw.rectangle((xmin, ymin, xmax, ymax), fill=(0, 0, 0))
#
image.save("Output.jpg")
