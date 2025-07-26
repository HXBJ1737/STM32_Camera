import sensor, image, time,screen
import pyb
import os
from pyb import Timer

img_dir1 = "/img/QVGA"
img_dir2 = "/img/VGA"
img_drawing_board=sensor.alloc_extra_fb(320,240,sensor.RGB565)
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

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)


# sensor.set_contrast(0) # 设置对比度，范围-3到+3
# sensor.set_brightness(0) # 设置亮度，范围-3到+3
# sensor.set_saturation(0) # 设置饱和度，范围-3到+3

sensor.set_auto_gain(True)
sensor.set_auto_exposure(True)
sensor.set_auto_whitebal(True)

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
def take_picture():
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



def main():
    mode = 0
    vh=0
    img_files=None
    current_img = 0  # 当前显示的图片索引
    screen.init(rotation=3)
    is_VGA=0
    K0 = NonBlockingButton('P6',timer=4)
    K1 = NonBlockingButton('P7',timer=2)
    K2 = NonBlockingButton('P9',timer=3)
    if vh:
        sensor.set_vflip(True) # 垂直翻转
        sensor.set_hmirror(True) # 水平镜像
    else:
        sensor.set_vflip(False)
        sensor.set_hmirror(False)

    while True:
        while mode== 0:
            img_drawing_board.draw_rectangle(0,0,320,240,fill=True,color=(0,0,0))
            img_drawing_board.draw_string(10,50,'In Camera mode, K0: Taking Picture ; K1: Into Album ; K2: Adjust Resolution',scale=(1),color=(0,255,255),mono_space=False)
            img_drawing_board.draw_string(10,65,'In Album mode, K0: Remove Picture ; K1: Into Camera; K2: Next Picture ',scale=(1),color=(0,255,255),mono_space=False)
            img_drawing_board.draw_string(10,80,'OV5640 : short press K0;          OV7725 or OV2640 : long press K0',scale=(1),color=(100,100,150),mono_space=False)
            img_drawing_board.draw_string(60,100,'Press K0 into Camera mode',scale=(2),color=(0,255,255),mono_space=False)
            img_drawing_board.draw_string(60,140,'Press K1 into Album  mode',scale=(2),color=(0,255,255),mono_space=False)
            img_drawing_board.draw_string(120,200,str(time.ticks_ms()),scale=(2),color=(0,100,255),mono_space=False)
            screen.display(img_drawing_board)
            if K0.is_short_pressed():
                print("K0 pressed!")
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
                print("K1 pressed!")
                current_img=0
                img_files = [f for f in os.listdir(img_dir1) if f.lower().endswith('.jpg')]
                img_files.sort()
                if not img_files:
                    raise Exception("No images found in %s" % img_dir1)
                print("%s/%s" % (img_dir1, img_files[current_img]))
                img = image.Image("%s/%s" % (img_dir1, img_files[current_img]))
                screen.display(img)
                mode = 2

        while mode==1:
            img = sensor.snapshot() #获取感光器画面
            img_drawing_board.draw_rectangle(0,0,320,240,fill=True,color=(0,0,0))
            img_drawing_board.draw_string(10,10,'Camera 2x'if is_VGA else 'Camera 1x',scale=(1),color=(0,255,50),mono_space=False)
            img_drawing_board.draw_string(10,225,'K0 : Taking Picture   K1 : Into Album   K2 : Adjust Resolution  K2(long): Back',scale=(1),color=(0,255,255),mono_space=False)
            img_drawing_board.b_or(img)
            screen.display(img_drawing_board)
            if K2.is_long_pressed():
                mode = 0
            if K0.is_short_pressed():
                print("K0 pressed!")
                take_picture()
            if K2.is_short_pressed():
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
            if K1.is_short_pressed():
                print("K1 pressed!")
                current_img=0
                img_files = [f for f in os.listdir(img_dir1) if f.lower().endswith('.jpg')]
                img_files.sort(reverse=True)
                if not img_files:
                    raise Exception("No images found in %s" % img_dir1)
                print("%s/%s" % (img_dir1, img_files[current_img]))
                img = image.Image("%s/%s" % (img_dir1, img_files[current_img]))
                screen.display(img)
                mode = 2
        while mode == 2:
            if K0.is_short_pressed():
                print("K0 pressed!")
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

            if K2.is_short_pressed():
                print("K2 pressed!")
                current_img = (current_img + 1) % len(img_files)
                try:
                    img = image.Image("%s/%s" % (img_dir1, img_files[current_img]))
                    screen.display(img)
                    print("%s/%s" % (img_dir1, img_files[current_img]))
                except Exception as e:
                    print("Failed to display image:", e)

            if K1.is_short_pressed():
                print("K1 pressed!")
                mode = 1



if __name__=="__main__":
    main()
