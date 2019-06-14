import numpy as np # массивы
import cv2 # компьютерное зрение
import argparse # параметры запуска скрипта
from math import sqrt # вычисление квадратного корня
import datetime # дата
import time # задержка/пауза
import matplotlib.pyplot as plt # изображение с координатными осями
import serial # последовательный порт
from Config import config # файл с координатами полезной области
from Config import max # файл с максимальным размером
from tkinter import * # окно с кнопкой
import imutils

ap = argparse.ArgumentParser(description='Программа определения превышения габаритов.')
ap.add_argument("-i", "--image", required = False, help = "Имя изображения. Режим работы с изображением.")
ap.add_argument("-c", "--camera", type = int, required = False, help = "Номер Web камеры в системе. Рабочий режим.")
ap.add_argument("-s", "--setka", type = int, required = False, help = "Выделение полезной области.")
ap.add_argument("-r", "--razmer", type = int, required = False, help = "Выделение макимального размера предмета.")
args = vars(ap.parse_args())

print(args)

# старт мотора
def motor_stop(stop):
    ser.write("1".encode())
    print("Движение: ", stop)

# стоп мотора
def motor_start(start):
    time.sleep(2)
    ser.write("0".encode())
    print("Движение: ", start)

    '''
    # Настройка параметров последовательного порта
    ser = serial.Serial()
    ser.port = "/dev/ttyACM0"
    ser.baudrate = 9600
    ser.bytesize = serial.EIGHTBITS     #number of bits per bytes
    ser.parity = serial.PARITY_NONE     #set parity check: no parity
    ser.stopbits = serial.STOPBITS_ONE  #number of stop bits
    #ser.timeout = None                 #block read
    ser.timeout = 1                     #non-block read
    #ser.timeout = 2                    #timeout block read
    ser.xonxoff = False                 #disable software flow control
    ser.rtscts = False                  #disable hardware (RTS/CTS) flow control
    ser.dsrdtr = False                  #disable hardware (DSR/DTR) flow control
    ser.writeTimeout = 2                #timeout for write
    ser = serial.Serial('/dev/ttyACM0', 9600)
    print('Enter 1 or 0...')
    ser.write("1")
    '''

# окно при превышении габаритов
def okno():
    root = Tk()
    root.title("ВНИМАНИЕ!")
    root.geometry("300x250")

    # запуск ленты
    def ex(event):
        root.destroy()
        motor_start("СТАРТ")

    text = Text(width=50, height=10)
    text.pack()
    text.insert(1.0, "Внимание!\nПревышение допустимых габатитов.\nУберите объект и нажмите Возобновить")

    btn = Button(root,
            text="Возобновить", # текст кнопки
            background="#555",  # фоновый цвет кнопки
            foreground="#ccc",  # цвет текста
            padx="20",          # отступ от границ до содержимого по горизонтали
            pady="8",           # отступ от границ до содержимого по вертикали
            font="16"           # высота шрифта
            )
    # действие по нажатию кнопки
    btn.bind("<Button-1>", ex)
    btn.pack()

    root.mainloop()

# Изображение на сетке для калибровки
def setka(image):
    plt.imshow(image)
    plt.show()

# Изменение разрешения картинки
def resize(image):
    scale_percent = 10 # процент от оригинального изображения
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    dim = (width, height)
    image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
    return image

# Обрезка изображения
def obrez(image):
    X1 = config.X1_AREA
    X2 = config.X2_AREA
    Y1 = config.Y1_AREA
    Y2 = config.Y2_AREA
    #width = int(image.shape[1])
    #height = int(image.shape[0])
    #roi = image[int(height/3):int(height/3)*2,0:width] # img[y:y+h, x:x+w]
    roi = image[Y1:Y1+Y2, X1:X1+X2] # img[y:y+h, x:x+w]
    return roi

# Маска для изображения полезной области
def region(image):
    X1 = config.X1_AREA
    X2 = config.X2_AREA
    Y1 = config.Y1_AREA
    Y2 = config.Y2_AREA
    # границы области на изображении
    #width = int(image.shape[1])
    #height = int(image.shape[0])
    #cv2.line(image, (0, int(height/3)), (width, int(height/3)), (255, 0, 0), 5)
    #cv2.line(image, (0, int(height/3)*2), (width, int(height/3)*2), (255, 0, 0), 5)

    # границы полезной области
    #polygons = np.array([[(0, int(height/3)), (width, int(height/3)), (width, int(height/3)*2), (0, int(height/3)*2)]])
    polygons = np.array([[(X1, Y1), (X1+X2, Y1), (X1+X2, Y1+Y2), (X1, Y1+Y2)]])
    mask = np.zeros_like(image)
    cv2.fillPoly(mask, polygons, 255)
    masked_image = cv2.bitwise_and(image, mask)
    return masked_image

def previshenie(storona, edge1, edge2):
    #середина вектора = сторона / 2
    seredina_oblasti = (config.X2_AREA - config.X1_AREA) / 2
    #print("Середина области: ", seredina_oblasti)
    #print("Середина детали: ", storona)

    # пересечение центра области
    # +- несколько пикселей для погрешности
    if (storona > seredina_oblasti-5) & (storona < seredina_oblasti+5):

        # проверяем на превышение
        if (edge1 >= max.MAX) | (edge2 >= max.MAX):
            print('Превышение допустимого размера!!!')
            # запись о превышении ф файл
            handle = open("logs/Report.log", "a")
            now = datetime.datetime.now()
            handle.write(now.strftime("%d-%m-%Y %H:%M:%S") + " Превышение допустимого размера!!!\n")
            handle.close()

            # сохранение изображения с превышением
            cv2.imwrite("Output/truba-" + now.strftime("%d-%m-%Y %H:%M:%S") + ".jpg", img)

            # остановка движения ленты
            motor_stop("СТОП")
            # сообщение о превышении для дальнейшего устранения
            okno()

            #print('Длина стороны 1: ', np.int0(edge1))
            #print('Длина стороны 2: ', np.int0(edge2))

            #print('Координаты вершин (approx): \n', approx)
            #print('Количество вершин: ', len(approx))
            #print('Количество четырехугольников: ', format(i))
        return

# Режим видео
def video_rezhim(cap):
    while(True):
        ret, frame = cap.read()
        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()

# Обработка изображения
def image_rezhim(image):
    img = np.copy(image)

    # отфильтровать небольше линии
    #kernel = np.ones((5,5),np.float32)/25
    #img = cv2.filter2D(img,-1,kernel)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    #canny = cv2.Canny(gray, 50, 150)
    canny = cv2.Canny(blur, 40, 10)

    ret, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)

    #contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    # для количества четырехугольников
    i = 0

    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.04*cv2.arcLength(cnt, True), True)
        #print len(approx)
        if len(approx) == 4:
            i += 1
            cv2.drawContours(img, [cnt], 0, (0, 255, 0), 3)

            # меняем форму массива с (4,1,2) на (4,2)
            approx = approx.reshape((4, 2))

            # вычисление координат двух векторов, являющихся сторонам прямоугольника
            edge1 = sqrt((approx[1][0] - approx[0][0])**2 + (approx[1][1] - approx[0][1])**2)
            edge2 = sqrt((approx[2][0] - approx[1][0])**2 + (approx[2][1] - approx[1][1])**2)

            # середина вектора по коррдинате X
            #serX1 = approx[1][0] - approx[0][0]
            #serX2 = approx[2][0] - approx[1][0]
            #print("approx1", approx[1][0])
            #print("approx0", approx[0][0])
            #print("serX1", serX1)
            #print("serX2", serX2)

            # рисуем маленький кружок в вершинах прямоугольника
            cv2.circle(img, (approx[0][0],approx[0][1]), 5, (0, 0, 255), 2)
            cv2.circle(img, (approx[1][0],approx[1][1]), 5, (0, 0, 255), 2)
            cv2.circle(img, (approx[2][0],approx[2][1]), 5, (0, 0, 255), 2)
            cv2.circle(img, (approx[3][0],approx[3][1]), 5, (0, 0, 255), 2)

            # сравниваем длину двух сторон (большой и соседней маленькой, например)
            # ведем четырехугольник для остановки до середины экрана по бОльшей стороне
            if edge1 >= edge2:
                # координаты по X середины стороны
                dlina_vektora = (approx[1][0] + approx[0][0]) / 2
                previshenie(dlina_vektora, edge1, edge2)

            else:
                # координаты по X середины стороны
                dlina_vektora = (approx[2][0] + approx[1][0]) / 2
                previshenie(dlina_vektora, edge1, edge2)

        break

    #print('Количество контуров: ', format(len(contours)))

    # отображение общего количества четырехугольников на изображении
    text = "Found {} total rectangle". format(i)
    cv2.putText(img, text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    # границы области на изображении
    #width = img.shape[1]
    #height = img.shape[0]
    #cv2.line(img, (0, int(height/3)), (width, int(height/3)), (255, 0, 0), 5)
    #cv2.line(img, (0, int(height/3)*2), (width, int(height/3)*2), (255, 0, 0), 5)

    # сохранение изображений
    #cv2.imshow('Contours', img)
    #cv2.imwrite("Contours.jpg", img)
    #cv2.imshow('Gray', gray)
    #cv2.imwrite("Gray.jpg", gray)
    #cv2.imshow('Blur', blur)
    #cv2.imwrite("Blur.jpg", blur)
    #cv2.imshow('Canny', canny)
    #cv2.imwrite("Canny.jpg", canny)

    return img

# Выбор режима работы в зависимости от параметров запуска:

if args["image"] is not None:
    image = cv2.imread(args["image"])
    #cv2.imwrite("Original.jpg", image)
    cv2.imshow('Original', image)

    image = obrez(image)
    img = image_rezhim(image)
    cv2.imshow('Contours', img)
    cv2.waitKey()
    cv2.destroyAllWindows()

if args["camera"] is not None:
    cap = cv2.VideoCapture(args["camera"])

    # инициализация последовательного порта
    ser = serial.Serial('/dev/ttyACM0',9600,timeout=5)
    ser.isOpen()
    motor_start("СТАРТ")

    while(cap.isOpened()):
        _, frame = cap.read()

        cv2.imshow('Original', frame)

        image = obrez(frame)
        #cv2.imshow('Contours', image)
        img = image_rezhim(image)
        cv2.imshow('Contours', img)

        # наложение изображений
        #combo_image = cv2.addWeighted(frame, 1, img, 0.8)
        #cv2.imshow("Out", combo_image)
        # или
        #vis = np.concatenate((frame, img), axis=1)
        #cv2.imwrite('out.png', vis)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if args["setka"] is not None:
    cap = cv2.VideoCapture(args["setka"])

    while(cap.isOpened()):
        _, frame = cap.read()

        cv2.imshow('Original', frame)

        k = cv2.waitKey(1)

        if k%256 == ord('q'):
            break
        elif k%256 == ord('s'):
            image = np.copy(frame)
            r = cv2.selectROI(image)
            print(r)
            # выделение полезной области
            imCrop = image[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])] # img[y:y+h, x:x+w]
            width = int(imCrop.shape[1])
            height = int(imCrop.shape[0])
            print('Размер области: ', width, height)
            # вывод изображения полезной области
            cv2.destroyAllWindows()
            cv2.imshow("Image", imCrop)
            # запись координат в файл полезной области
            handle = open("Config/config.py", "w")
            handle.write("X1_AREA = " + str(r[0]) + "\n"
                        "X2_AREA = " + str(r[2]) + "\n"
                        "Y1_AREA = " + str(r[1]) + "\n"
                        "Y2_AREA = " + str(r[3]))
            handle.close()

    cap.release()
    cv2.destroyAllWindows()

if args["razmer"] is not None:
    cap = cv2.VideoCapture(args["razmer"])

    while(cap.isOpened()):
        _, frame = cap.read()

        #cv2.imshow('Original', frame)
        img = obrez(frame)
        cv2.imshow('Obrez', img)

        k = cv2.waitKey(1)

        if k%256 == ord('q'):
            break
        elif k%256 == ord('s'):
            image = np.copy(img)
            r = cv2.selectROI(image)
            print(r)
            # выделение максимального размера предмета
            imCrop = image[int(r[1]):int(r[1]+r[3]), int(r[0]):int(r[0]+r[2])] # img[y:y+h, x:x+w]
            width = int(imCrop.shape[1])
            height = int(imCrop.shape[0])
            print('Размер области: ', width, height)
            # вывод изображения максимального размера предмета
            cv2.destroyAllWindows()
            cv2.imshow("Image", imCrop)
            # запись максимального количества пикселей
            handle = open("Config/max.py", "w")
            handle.write("MAX = " + str(r[2]))
            handle.close()

    cap.release()
    cv2.destroyAllWindows()
