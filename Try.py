import cv2
import boto3
import re

# Load the image
image = cv2.imread('./Images/21.jpg')

# Convert the image to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Apply Otsu's thresholding
threshold, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

print(f"threshold:{threshold}")
print(f"_:{_}")

# Detect the text regions
contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

# Iterate over the text regions
for contour in contours:
    print(f"contour:{contour}")
#     # Get the rectangle bounding the text region
    x, y, w, h = cv2.boundingRect(contour)

    print(f"x:{x},y:{y},w:{w},h:{h}")
#
#     # Extract the text region
    region = image[y:y+h, x:x+w]
#
#     # Use AWS Rekognition to detect the text in the region
    rekoginition = boto3.client('rekognition')
    response = rekoginition.detect_text(Image={'S3Object': {'Bucket': 'hdfctests','Name': '21.jpg'}})


# rekoginition = boto3.client("rekognition")
#
# response = rekoginition.detect_text(
#     Image={
#         'S3Object': {
#             'Bucket': 'hdfctests',
#             'Name': '21.jpg'
#         }
#     }
# )

print(f"text['Detections']:{response['TextDetections']}")

textDetections = response['TextDetections']

regex = ("^[2-9]{1}[0-9]{3}\\" +
             "s[0-9]{4}\\s[0-9]{4}$")
p = re.compile(regex)

# Iterate over the detected text lines
for text in textDetections:
    # print(f"text:{text}")
    if text['Type'] == "LINE":
        if (re.search(p, text['DetectedText'])):
            print(f"Matched Text:{text}")
            print(f"Aadhar Number:{text['DetectedText']}")

            digits = list(text['DetectedText'])
            print(f"digits:{digits}")
            print(f"digits length:{len(digits)}")
            digit_w = w / len(digits)

            print(f"digit_w:{digit_w}")
            digit_x=0
            digit_y=0
            digit_h=0
            for i, digit in enumerate(digits):
                digit_x = x + i * digit_w
                digit_y = y
                digit_h = h

                print(f"digit_x:{digit_x}")
                print(f"digit_y:{digit_y}")
                print(f"digit_h:{digit_h}")

            cv2.rectangle(image, (digit_x, digit_y), (digit_x + digit_w, digit_y + digit_h), (0, 0, 0), -1)

            # if(len(text['DetectedText']) == 8):
            #     print(f"Here")

#     # If the text is an 8-digit number, mask it digit by digit
#     if len(text['DetectedText']) == 8 and text['DetectedText'].isdigit():
#         # Split the number into individual digits
#         digits = list(text['DetectedText'])
#
#         # Calculate the width of each digit
#         digit_w = w / len(digits)
#
#         # Iterate over the digits
#         for i, digit in enumerate(digits):
#             # Calculate the position of the digit
#             digit_x = x + i * digit_w
#             digit_y = y
#             digit_h = h
#
#             # Draw a black rectangle over the digit
#             cv2.rectangle(image, (digit_x, digit_y), (digit_x + digit_w, digit_y + digit_h), (0, 0, 0), -1)

# Save the image with the masked text
# cv2.imwrite('aadhar_card_masked.jpg', image)
