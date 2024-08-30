# Import required packages
import cv2
import pytesseract
import matplotlib.pyplot as plt

# Mention the installed location of Tesseract-OCR in your system
pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

# Read the image from which text needs to be extracted
img = cv2.imread('./files/to_img/cci1010_0OTSU.png')

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


# Performing OTSU threshold
ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

# dilation parameter, bigger means less rectangle
rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))

# Applying dilation on the threshold image
dilation = cv2.dilate(thresh1, rect_kernel, iterations = 1)

# Finding contours
contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)

# Creating a copy of image
im2 = gray.copy()


cnt_list=[]
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)

    # Drawing a rectangle on the copied image
    rect = cv2.rectangle(im2, (x, y), (x + w, y + h), (0, 255, 0), 5)
    cv2.circle(im2,(x,y),8,(255,255,0),8)

    # Cropping the text block for giving input to OCR
    cropped = im2[y:y + h, x:x + w]

    # Apply OCR on the cropped image
    config_pytesseract = r'--tessdata-dir assets/tessdata -l por --oem 2 --psm 6'
    text = pytesseract.pytesseract.image_to_string(image=cropped, lang='por', config=config_pytesseract)

    cnt_list.append([x,y,text])


# This list sorts text with respect to their coordinates, in this way texts are in order from top to down
sorted_list = sorted(cnt_list, key=lambda x: x[1])

# A text file is created 
file = open("recognized.txt", "w+")
file.write("")
file.close()


for x,y,text in sorted_list:
    # Open the file in append mode
    file = open("recognized.txt", "a")

    # Appending the text into the file
    file.write(text)
    file.write("\n")

    # Close the file
    file.close()


# read image 
rgb_image = cv2.resize(im2, (0, 0), fx = 0.4, fy = 0.4)
dilation = cv2.resize(dilation, (0, 0), fx = 0.4, fy = 0.4)
#thresh1 = cv2.resize(thresh1, (0, 0), fx = 0.4, fy = 0.4)

# show the image, provide the window name first
#cv2.imshow('thresh1', thresh1)
cv2.imshow('dilation', dilation)
cv2.imshow('gray', gray)

# add wait key. window waits until the user presses a key
cv2.waitKey(0)
# and finally destroy/close all open windows
cv2.destroyAllWindows()