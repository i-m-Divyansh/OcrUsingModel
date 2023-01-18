import cv2

def rotateImageIfInverted():
    img = cv2.imread("./temp_images/21_0.jpg")
    print(f"type: {type(img)}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


    rotations = [[gray, 1],
                 [cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE), 2],
                 [cv2.rotate(gray, cv2.ROTATE_180), 3],
                 [cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE), 4],
                 [cv2.GaussianBlur(gray, (5, 5), 0), 1],
                 [cv2.GaussianBlur(cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE), (5, 5), 0), 2],
                 [cv2.GaussianBlur(cv2.rotate(gray, cv2.ROTATE_180), (5, 5), 0), 3],
                 [cv2.GaussianBlur(cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE), (5, 5), 0), 4]]

    for rotation in rotations:
        print(f"rotation:{rotation}")
        if(True):
            checkRotationType(rotation[1],img)


def checkRotationType(rtype,img):
    print(f"rtype:{rtype}")

    if rtype == 2:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    elif rtype == 3:
        img = cv2.rotate(img, cv2.ROTATE_180)
    elif rtype == 4:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

    # if rtype == 2:
    #     img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    # elif rtype == 3:
    #     img = cv2.rotate(img, cv2.ROTATE_180)
    # elif rtype == 4:
    #     img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)



    cv2.imwrite("./output/test.jpg", img)




rotateImageIfInverted();