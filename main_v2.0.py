# author: 恒星不见&ZhangJie
# date: 2025-08-13
import sensor, image, time,screen
import pyb
import os
from pyb import Timer
import random

class NonBlockingButton:
    def __init__(self, pin_name, debounce_time=20, timer=4, long_press_time=1000):
        """
        初始化非阻塞按键检测（解决单击与长按冲突）
        :param pin_name: 按键连接的引脚名称，如 'P0'
        :param debounce_time: 消抖时间(ms)
        :param timer: 使用的定时器编号
        :param long_press_time: 长按判定时间(ms)
        """
        self.button = pyb.Pin(pin_name, pyb.Pin.IN, pyb.Pin.PULL_UP)
        self.last_state = self.button.value()
        self.current_state = self.last_state
        self.debounce_time = debounce_time
        self.last_debounce_time = 0
        self.pressed = False
        self.released = False
        self.long_pressed = False
        self.short_pressed = False
        self.last_press_time = 0
        self.last_release_time = 0
        self.long_press_time = long_press_time
        self.timer_num = timer
        self.waiting_for_release = False  # 标记是否在等待释放以确定短按

        # 创建定时器中断
        self.timer = Timer(timer, freq=1000)
        self.timer.callback(self._update_button_state)

    def _update_button_state(self, t):
        """定时器中断回调函数"""
        reading = self.button.value()

        # 消抖处理
        if reading != self.last_state:
            self.last_debounce_time = pyb.millis()

        if (pyb.millis() - self.last_debounce_time) > self.debounce_time:
            if reading != self.current_state:
                self.current_state = reading

                # 按键按下（下降沿）
                if self.current_state == 0:
                    self.pressed = True
                    self.last_press_time = pyb.millis()
                    self.waiting_for_release = True

                # 按键释放（上升沿）
                else:
                    self.released = True
                    self.last_release_time = pyb.millis()

                    # 如果在长按触发前释放，则是短按
                    if self.waiting_for_release:
                        self.short_pressed = True

                    self.waiting_for_release = False

        # 长按检测（仅当按键仍被按住且未触发过长按）
        if (self.current_state == 0 and
            self.waiting_for_release and
            (pyb.millis() - self.last_press_time) > self.long_press_time):
            self.long_pressed = True
            self.waiting_for_release = False  # 防止重复触发

        self.last_state = reading

    def is_pressed(self):
        """检测按键按下事件（按下瞬间）"""
        if self.pressed:
            self.pressed = False
            return True
        return False

    def is_short_pressed(self):
        """检测短按事件（释放后才确定）"""
        if self.short_pressed:
            self.short_pressed = False
            return True
        return False

    def is_long_pressed(self):
        """检测长按事件"""
        if self.long_pressed:
            self.long_pressed = False
            return True
        return False

    def is_released(self):
        """检测按键释放事件"""
        if self.released:
            self.released = False
            return True
        return False

    def press_duration(self):
        """获取当前按键按下的持续时间"""
        if self.current_state == 0:
            return pyb.millis() - self.last_press_time
        return 0

    def deinit(self):
        """释放资源"""
        self.timer.callback(None)

class ProgressBar:
    def __init__(self, x, y, width, height, color=(0, 255, 0), bg_color=(0, 0, 0), border=2):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.bg_color = bg_color
        self.border = border
        self.progress = 0  # 0-100

    def set_progress(self, percent):
        self.progress = max(0, min(100, percent))  # 限制在0-100之间

    def draw(self, img):
        # 绘制背景
        img.draw_rectangle(self.x, self.y, self.width, self.height, color=self.bg_color, fill=True)

        # 绘制边框
        img.draw_rectangle(self.x, self.y, self.width, self.height, color=(0, 0, 0), thickness=self.border)

        # 计算进度条长度
        progress_width = int((self.width - 2*self.border) * (self.progress / 100))

        # 绘制进度
        if progress_width > 0:
            img.draw_rectangle(self.x + self.border,
                             self.y + self.border,
                             progress_width,
                             self.height - 2*self.border,
                             color=self.color,
                             fill=True)

        #绘制百分比文本
        text = "%d%%" % self.progress
        text_x = self.x + (self.width - 40) // 2
        text_y = self.y + (self.height - 8) // 2
        img.draw_string(text_x, text_y, text, color=(255, 255, 255), scale=1)


img_dir1 = "/img/QVGA"
img_dir2 = "/img/VGA"
img_drawing_board=sensor.alloc_extra_fb(320,240,sensor.RGB565)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
# sensor.set_contrast(0) # 设置对比度，范围-3到+3
# sensor.set_brightness(0) # 设置亮度，范围-3到+3
# sensor.set_saturation(0) # 设置饱和度，范围-3到+3
sensor.set_auto_gain(True)
sensor.set_auto_exposure(True)
sensor.set_auto_whitebal(True)
clock = time.clock()

def get_next_filename(dir_path, extension='.jpg',):
    # 获取目录下所有匹配的文件
    existing_files = [f for f in os.listdir(dir_path) if f.endswith(extension)]

    # 提取最大序号
    max_num = 0
    for f in existing_files:
        try:
            num = int(f[0:-len(extension)])
            if num > max_num:
                max_num = num
        except:
            pass

    # 返回新文件名（序号+1）
    new_num = max_num + 1
    return "{:03d}{}".format(new_num, extension)
def take_photo():
    path=get_next_filename(img_dir1)
    filename = img_dir1+'/'+path
    img = sensor.snapshot() #获取感光器画面
    img.save(filename)
    img_drawing_board.draw_rectangle(0,0,320,240,fill=True,color=(0,0,0))
    img_drawing_board.draw_string(10,200,'Saved '+filename,scale=(1),color=(255,0,0),mono_space=False)
    img_drawing_board.b_or(img)
    screen.display(img_drawing_board)
    print("Saved:", filename)
    pyb.LED(3).on()
    time.sleep(0.5)
    pyb.LED(3).off()


def convert_ms_to_hms(x):
    total_seconds = x / 1000
    hours = int(total_seconds // 3600)
    remaining_seconds = total_seconds % 3600
    minutes = int(remaining_seconds // 60)
    seconds = int(remaining_seconds % 60)
    # milliseconds = int((x % 1000))  # 如果需要保留毫秒部分

    # 格式化为两位数，例如 01:05:23
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # 如果需要包含毫秒
    # return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:02d}"



def app_init():
    progress_bar = ProgressBar(50, 180, 220, 20, color=(0, 255, 0))
    progress = 0
    img_drawing_board.draw_rectangle(0,0,320,240,fill=True,color=(0,0,0))
    while True:
        progress += 1
        if progress > 100:
            break
        if progress % 6==0:
            img_drawing_board.draw_string(40,progress//6*10,f'[{time.ticks_ms()}] Initing  {progress*random.randint(1, 1000):05d} | Author : hxbj1737@outlook.com  ',scale=(1),color=(255,0,255),mono_space=False)
        progress_bar.set_progress(progress)
        progress_bar.draw(img_drawing_board)
        screen.display(img_drawing_board)

    # for line in range(1,20,1):
    #     time.sleep(0.5)
    #     img_drawing_board.draw_string(20,line*10,f'Initing                       {line}|  Author : hxbj1737@outlook.com  ',scale=(1),color=(255,0,255),mono_space=False)
    #     screen.display(img_drawing_board)
    time.sleep(0.1)

def main():
    mode = 0
    vh=0
    img_files=None
    current_img = 0  # 当前显示的图片索引
    screen.init(rotation=3)
    is_VGA=0
    last_x=0    #上一次x坐标
    last_y=0    #上一次y坐标
    first_time_press=True   #第一次按下（抬笔后线条不连续）
    K0 = NonBlockingButton('P6',timer=4)
    K1 = NonBlockingButton('P7',timer=2)
    K2 = NonBlockingButton('P9',timer=3)
    if vh:
        sensor.set_vflip(True) # 垂直翻转
        sensor.set_hmirror(True) # 水平镜像
    else:
        sensor.set_vflip(False)
        sensor.set_hmirror(False)
    app_init()
    while True:
        while mode== 0:
            img_drawing_board.draw_rectangle(0,0,320,240,fill=True,color=(0,0,0))
            img_drawing_board.draw_string(20,10,'Init successed , This is Index page  |  Author : hxbj1737@outlook.com  ',scale=(1),color=(255,0,255),mono_space=False)
            img_drawing_board.draw_string(55,30,'In Camera mode, K0: Take photo ; K1: Adjust Resolution ',scale=(1),color=(0,255,255),mono_space=False)
            img_drawing_board.draw_string(55,45,'In Album mode, K0: Remove Picture ; K1: Next Picture ',scale=(1),color=(0,255,255),mono_space=False)
            img_drawing_board.draw_string(55,60,'In Draw mode,  K0: Take Picture ; K1: Clear  ',scale=(1),color=(0,255,255),mono_space=False)
            img_drawing_board.draw_string(55,75,'In ALL mode,  K2(short) : Back Index ',scale=(1),color=(0,255,255),mono_space=False)
            img_drawing_board.draw_string(55,95,'OV5640 : K0(short) ; OV7725 or OV2640 : K0(long)',scale=(1),color=(255,255,150),mono_space=False)
            img_drawing_board.draw_string(55,110,'Press K0 into Camera mode',scale=(2),color=(0,255,0),mono_space=False)
            img_drawing_board.draw_string(55,130,'Press K1 into Album  mode',scale=(2),color=(0,255,0),mono_space=False)
            img_drawing_board.draw_string(55,150,'Press K2 into  Draw   mode',scale=(2),color=(0,255,0),mono_space=False)
            img_drawing_board.draw_rectangle(70,190,170,40,color=(255,255,255))
            img_drawing_board.draw_string(80,200,'Run time : '+convert_ms_to_hms(time.ticks_ms()),scale=(2),color=(0,100,255),mono_space=False)
            screen.display(img_drawing_board)
            if K0.is_short_pressed():
                mode=1
            if K0.is_long_pressed():
                vh=1-vh
                if vh:
                    sensor.set_vflip(True) # 垂直翻转
                    sensor.set_hmirror(True) # 水平镜像
                else:
                    sensor.set_vflip(False)
                    sensor.set_hmirror(False)
                mode=1
            if K1.is_short_pressed():
                current_img=0
                img_files = [f for f in os.listdir(img_dir1) if f.lower().endswith('.jpg')]
                img_files.sort()
                if not img_files:
                    raise Exception("No images found in %s" % img_dir1)
                print("%s/%s" % (img_dir1, img_files[current_img]))
                img = image.Image("%s/%s" % (img_dir1, img_files[current_img]))
                screen.display(img)
                mode = 2
            if K2.is_short_pressed():
                img_drawing_board.draw_rectangle(0,0,320,240,fill=True,color=(255,255,255))
                mode =3

        while mode==1:
            img = sensor.snapshot() #获取感光器画面
            img_drawing_board.draw_rectangle(0,0,320,240,fill=True,color=(0,0,0))
            img_drawing_board.draw_string(10,10,'Camera 2x'if is_VGA else 'Camera 1x',scale=(1),color=(0,255,50),mono_space=False)
            img_drawing_board.draw_string(10,225,'K0 : Taking Picture             K1 : Adjust Resolution             K2 :  Back Index',scale=(1),color=(0,255,255),mono_space=False)
            img_drawing_board.b_or(img)
            screen.display(img_drawing_board)
            if K0.is_short_pressed():
                take_photo()

            if K1.is_short_pressed():
                is_VGA=1-is_VGA
                if is_VGA:
                    sensor.reset()
                    sensor.set_pixformat(sensor.RGB565)
                    sensor.set_framesize(sensor.VGA)
                    sensor.set_windowing(0,0,320,240)
                    if vh:
                        sensor.set_vflip(True) # 垂直翻转
                        sensor.set_hmirror(True) # 水平镜像
                else:
                    sensor.reset()
                    sensor.set_pixformat(sensor.RGB565)
                    sensor.set_framesize(sensor.QVGA)
                    sensor.set_windowing(0,0,320,240)
                    if vh:
                        sensor.set_vflip(True) # 垂直翻转
                        sensor.set_hmirror(True) # 水平镜像

            if K2.is_short_pressed():
                mode = 0

        while mode == 2:
            if K0.is_short_pressed():
                pyb.LED(2).on()
                file_path="%s/%s" % (img_dir1, img_files[current_img])
                try:
                    os.remove(file_path)
                    print("Deleted:", file_path)
                except OSError as e:
                    print("Error deleting file:", e)
                img_files = [f for f in os.listdir(img_dir1) if f.lower().endswith('.jpg')]
                img_files.sort(reverse=True)
                pyb.LED(2).off()
                current_img = (current_img) % len(img_files)
                try:
                    img = image.Image("%s/%s" % (img_dir1, img_files[current_img]))
                    screen.display(img)
                    print("%s/%s" % (img_dir1, img_files[current_img]))
                except Exception as e:
                    print("Failed to display image:", e)

            if K1.is_short_pressed():
                current_img = (current_img + 1) % len(img_files)
                try:
                    img = image.Image("%s/%s" % (img_dir1, img_files[current_img]))
                    screen.display(img)
                    print("%s/%s" % (img_dir1, img_files[current_img]))
                except Exception as e:
                    print("Failed to display image:", e)

            if K2.is_short_pressed():
                mode = 0


        while mode == 3:
            if screen.press:
                if first_time_press:
                    img_drawing_board.draw_line(screen.x,screen.y,screen.x,screen.y,color=(0,0,0),thickness=3)
                    last_x=screen.x
                    last_y=screen.y
                    first_time_press=False
                else:
                    img_drawing_board.draw_line(screen.x,screen.y,last_x,last_y,color=(0,0,0),thickness=3)
                    last_x=screen.x
                    last_y=screen.y
            else:
                first_time_press=True
            screen.display(img_drawing_board)
            if K0.is_short_pressed():
                path=get_next_filename(img_dir1)
                filename = img_dir1+'/'+path
                img_drawing_board.save(filename)
                print("Saved:", filename)
                img_drawing_board.draw_string(10,200,'Saved '+filename,scale=(1),color=(255,0,0),mono_space=False)
                screen.display(img_drawing_board)
                pyb.LED(3).on()
                time.sleep(1)
                pyb.LED(3).off()
                img_drawing_board.draw_string(10,200,'Saved '+filename,scale=(1),color=(255,255,255),mono_space=False)

            if K1.is_short_pressed():
                img_drawing_board.draw_rectangle(0,0,320,240,fill=True,color=(255,255,255))
            if K2.is_short_pressed():
                mode = 0




if __name__=="__main__":
    main()
