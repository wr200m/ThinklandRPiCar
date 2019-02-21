import time
import RPi.GPIO as GPIO
import socket
import threading
import random



################################################################
#  直流电机引脚定义
PIN_MOTOR_LEFT_FORWARD = 20
PIN_MOTOR_LEFT_BACKWARD = 21
PIN_MOTOR_RIGHT_FORWARD = 19
PIN_MOTOR_RIGHT_BACKWARD = 26
PIN_MOTOR_LEFT_SPEED = 16
PIN_MOTOR_RIGHT_SPEED = 13

# 超声波引脚定义
PIN_ECHO = 0
PIN_TRIG = 1

# 彩色灯引脚定义
PIN_LED_R = 22
PIN_LED_G = 27
PIN_LED_B = 24

# 伺服电机引脚定义
PIN_FRONT_SERVER = 23
PIN_UP_DOWN_SERVER = 11
PIN_LEFT_RIGHT_SERVER = 9

# 避障脚定义
PIN_AVOID_LEFT_SENSOR = 12
PIN_AVOID_RIGHT_SENSOR = 17

# 巡线传感器引脚定义
PIN_TRACK_1 = 3  # counting From left, 1
PIN_TRACK_2 = 5  # 2
PIN_TRACK_3 = 4  # 3
PIN_TRACK_4 = 18  # 4

# 蜂鸣器
PIN_BUFFER = 8
#########################################################
# 宏定义特殊
HAVE_OBSTACLE = 0
NO_OBSTACLE = 1

SERVO_TOTAL_STEP = 18
ONE_PARA = 1
TWO_PARA = 2

DERECT_CALL = 1
THREAD_CALL = 0
RETURN_CALL = 2

LED_R = 0
LED_G = 1
LED_B = 2

OPEN = GPIO.HIGH
CLOSE= GPIO.LOW

class Car:
    def __init__(self):
        # 类的构造函数
        # 设置GPIO口为BCM编码方式
        GPIO.setmode(GPIO.BCM)
        # 忽略警告信息
        GPIO.setwarnings(False)
        # 初始化IO
        self.__init_level()
        #初始化 pwm
        self.__init_pwm()
        #函数列表，用于存放函数的容器
        self.Function_List = {}
        #用于灯光控制标志
        self.LED_FLAG = {}
        self.LED_FLAG[LED_R] = True
        self.LED_FLAG[LED_G] = True
        self.LED_FLAG[LED_B] = True

    def __init_level(self):#私有变量 外部不能调用
        """
        #  设置Io的输出方式：
        # 输出模式：即是具有上拉电阻
        # 输入模式：即是能获取电平的高低，在数字电路上高于二极管的导通电压为高，否则为低电平

        Parameters
        ----------
        """
        # 设置超声波电平
        GPIO.setup(PIN_ECHO, GPIO.IN)
        GPIO.setup(PIN_TRIG, GPIO.OUT)

        # 小车输出电平
        GPIO.setup(PIN_MOTOR_LEFT_FORWARD, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_MOTOR_LEFT_BACKWARD, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_MOTOR_RIGHT_FORWARD, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(PIN_MOTOR_RIGHT_BACKWARD, GPIO.OUT, initial=GPIO.LOW)

        # 小车速度
        GPIO.setup(PIN_MOTOR_LEFT_SPEED, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(PIN_MOTOR_RIGHT_SPEED, GPIO.OUT, initial=GPIO.HIGH)

        # 蜂鸣器电平
        GPIO.setup(PIN_BUFFER, GPIO.OUT, initial=GPIO.HIGH)

        # 彩灯输出设置
        GPIO.setup(PIN_LED_R, GPIO.OUT)
        GPIO.setup(PIN_LED_G, GPIO.OUT)
        GPIO.setup(PIN_LED_B, GPIO.OUT)

        # 舵机设置为输出模式
        GPIO.setup(PIN_FRONT_SERVER, GPIO.OUT)
        GPIO.setup(PIN_UP_DOWN_SERVER, GPIO.OUT)
        GPIO.setup(PIN_LEFT_RIGHT_SERVER, GPIO.OUT)

        # 避障传感器设置为输入模式
        GPIO.setup(PIN_AVOID_LEFT_SENSOR, GPIO.IN)
        GPIO.setup(PIN_AVOID_RIGHT_SENSOR, GPIO.IN)

        # 设置寻线传感器电平为输入
        GPIO.setup(PIN_TRACK_1, GPIO.IN)
        GPIO.setup(PIN_TRACK_2, GPIO.IN)
        GPIO.setup(PIN_TRACK_3, GPIO.IN)
        GPIO.setup(PIN_TRACK_4, GPIO.IN)

    def __init_pwm(self):#私有变量 外部不能调用
        """
        设置PWM，是脉冲宽度调制缩写
        它是通过对一系列脉冲的宽度进行调制，等效出所需要的波形（包含形状以及幅值），对模拟信号电平进行数字编码，
        也就是说通过调节占空比的变化来调节信号、能量等的变化，占空比就是指在一个周期内，信号处于高电平的时间占据整个信号周期的百分比
        通过设置占空比来控制车速、舵机的角度、灯光的亮度
        """

        # 初始化控制小车的PWM
        self.__pwm_left_speed  = GPIO.PWM(PIN_MOTOR_LEFT_SPEED, 2000)
        self.__pwm_right_speed = GPIO.PWM(PIN_MOTOR_RIGHT_SPEED, 2000)

        self.__pwm_left_speed.start(0)
        self.__pwm_right_speed.start(0)

        # 设置舵机的频率和起始占空比
        self.__pwm_front_servo_pos      = GPIO.PWM(PIN_FRONT_SERVER, 50)
        self.__pwm_up_down_servo_pos    =  GPIO.PWM(PIN_UP_DOWN_SERVER, 50)
        self.__pwm_left_right_servo_pos = GPIO.PWM(PIN_LEFT_RIGHT_SERVER, 50)

        self.__pwm_front_servo_pos.start(0)
        self.__pwm_up_down_servo_pos.start(0)
        self.__pwm_left_right_servo_pos.start(0)

        #设置灯的频率 从而控制其亮度
        # self.__pwm_led_r = GPIO.PWM(PIN_LED_R, 1000)
        # self.__pwm_led_g = GPIO.PWM(PIN_LED_G, 1000)
        # self.__pwm_led_b = GPIO.PWM(PIN_LED_B, 1000)
        #
        # self.__pwm_led_r.start(0)
        # self.__pwm_led_g.start(0)
        # self.__pwm_led_b.start(0)

    def __set_motion(self, left_forward, left_backward,
                    right_forward, right_backward,
                    speed_left, speed_right,
                    duration=0.0):
        """
        Helper function to set car wheel motions

        Parameters
        ----------
        * left_forward   : GPIO.HIGH or LOW
        * left_backward  : GPIO.HIGH or LOW
        * right_forward  : GPIO.HIGH or LOW
        * right_backward : GPIO.HIGH or LOW
        * speed_left     : int
            An integer [0,100] for left motors speed
        * speed_right    : int
            An integer [0,100] for right motors speed
        * duration       : float
            Duration of the motion.
            (default=0.0 - continue indefinitely until called again)
        Raises
        ------
        """
        GPIO.output(PIN_MOTOR_LEFT_FORWARD,   left_forward)
        GPIO.output(PIN_MOTOR_LEFT_BACKWARD,  left_backward)
        GPIO.output(PIN_MOTOR_RIGHT_FORWARD,  right_forward)
        GPIO.output(PIN_MOTOR_RIGHT_BACKWARD, right_backward)
        self.__pwm_left_speed.ChangeDutyCycle(speed_left)
        self.__pwm_right_speed.ChangeDutyCycle(speed_right)
        if duration > 0.0:
            time.sleep(duration)
            self.__pwm_left_speed.ChangeDutyCycle(0)
            self.__pwm_right_speed.ChangeDutyCycle(0)

    def __led_light(self, r, g, b):
        """
         __led_light

         Parameters
         ----------
         * r : bool
             - GPIO.HIGH  GPIO.LOW
         * g : bool
             - GPIO.HIGH  GPIO.LOW
         * b : bool
             - GPIO.HIGH  GPIO.LOW
        """
        GPIO.output(PIN_LED_R, r)
        GPIO.output(PIN_LED_G, g)
        GPIO.output(PIN_LED_B, b)

    def turn_on_led(self, led):
        """
         open_led:
         打开灯
         ____________
         Parameters
         ----------
         * led : int
             - LED_R  LED_G  LED_B三个选一个
         """
        print('open led')
        self.LED_FLAG[led] = True
        while self.LED_FLAG[led]:
            if led == LED_R:
                GPIO.output(PIN_LED_R, OPEN)
            elif led == LED_G:
                GPIO.output(PIN_LED_G, OPEN)
            else:
                GPIO.output(PIN_LED_B, OPEN)

    def turn_off_led(self, led):
        """
         close_led:
         关闭LED灯光
         ____________
         Parameters
         ----------
         * led : int
             - LED_R  LED_G  LED_B三个选一个
         """
        self.LED_FLAG[led] = False
        if led == LED_R:
            GPIO.output(PIN_LED_R, CLOSE)
        elif led == LED_G:
            GPIO.output(PIN_LED_G, CLOSE)
        else:
            GPIO.output(PIN_LED_B, CLOSE)

    def stop_all_wheels(self ,delay = 0):
        """
        Stop wheel movement
        """
        time.sleep(delay)

        self.__set_motion(GPIO.LOW, GPIO.LOW, GPIO.LOW, GPIO.LOW, 0, 0)

    def stop_completely(self ,delay = 0):
        """
        Completely stop the Car
        """
        time.time(delay)

        self.__pwm_left_speed.stop()
        self.__pwm_right_speed.stop()
        self.__pwm_servo_ultrasonic.stop()
        GPIO.cleanup()

    def run_forward(self, speed=50, duration=0.0):
        """
         Run forward

         Parameters
         ----------
         * speed : int
             - Speed of the motors. Valid range [0, 100]
         * duration : float
             - Duration of the motion.
             (default=0.0 - continue indefinitely until other motions are set)
         """
        self.__set_motion(GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.LOW,
                         speed, speed, duration)

    def run_reverse(self, speed=10, duration=0.0):
        """
        Run forward

        Parameters
        ----------
        * speed : int
            - Speed of the motors. Valid range [0, 100]
        * duration : float
            - Duration of the motion.
            (default=0.0 - continue indefinitely until other motions are set)

        Raises
        ------
        """
        self.__set_motion(GPIO.LOW, GPIO.HIGH, GPIO.LOW, GPIO.HIGH,
                         speed, speed, duration)

    def turn_left(self, speed=10, duration=0.0):
        """
        Turn left - only right-hand-side wheels run forward

        Parameters
        ----------
        * speed : int
            - Speed of the motors. Valid range [0, 100]
        * duration : float
            - Duration of the motion.
            (default=0.0 - continue indefinitely until other motions are set)

        Raises
        ------
        """
        self.__set_motion(GPIO.LOW, GPIO.LOW, GPIO.HIGH, GPIO.LOW,
                         0, speed, duration)

    def turn_right(self, speed=10, duration=0.0):
        """
        Turn right - only left-hand-side wheels run forward

        Parameters
        ----------
        * speed : int
            - Speed of the motors. Valid range [0, 100]
        * duration : float
            - Duration of the motion.
            (default=0.0 - continue indefinitely until other motions are set)

        Raises
        ------
        """
        self.__set_motion(GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.LOW,
                         speed, 0, duration)

    def spin_left(self, speed=10, duration=0.0):
        """
        Spin to the left in place

        Parameters
        ----------
        * speed : int
            - Speed of the motors. Valid range [0, 100]
        * duration : float
            - Duration of the motion.
            (default=0.0 - continue indefinitely until other motions are set)

        Raises
        ------
        """
        self.__set_motion(GPIO.LOW, GPIO.HIGH, GPIO.HIGH, GPIO.LOW,
                         speed, speed, duration)

    def spin_right(self, speed=10, duration=0.0):
        """
        Spin to the left in place

        Parameters
        ----------
        * speed : int
            - Speed of the motors. Valid range [0, 100]
        * duration : float
            - Duration of the motion.
            (default=0.0 - continue indefinitely until other motions are set)

        Raises
        ------
        """
        self.__set_motion(GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.HIGH,
                         speed, speed, duration)

    def distance_from_obstacle(self ,val = 0):
        """
        Measure the distance between ultrasonic sensor and the obstacle
        that it faces.

        The obstacle should have a relatively smooth surface for this
        to be effective. Distance to fabric or other sound-absorbing
        surfaces is difficult to measure.

        Returns
        -------
        * int
            - Measured in centimeters: valid range is 2cm to 400cm
        """
        # set HIGH at TRIG for 15us to trigger the ultrasonic ping
        print('check distance')
        #产生一个10us的脉冲
        distance = 0
        GPIO.output(PIN_TRIG, GPIO.LOW)
        time.sleep(0.02)
        GPIO.output(PIN_TRIG, GPIO.HIGH)
        time.sleep(0.000015)
        GPIO.output(PIN_TRIG, GPIO.LOW)
        time.sleep(0.00001)

        #等待接受
        if GPIO.input(PIN_ECHO):
            distance = -2
            return distance

        time1, time2 = time.time(), time.time()

        while not GPIO.input(PIN_ECHO):
            time1 = time.time()
            if time1 - time2 > 0.02:
                distance = -3
                break

        if distance == -3:
            return (distance)

        t1 = time.time()
        while GPIO.input(PIN_ECHO):
            time2 = time.time()
            if time2 - t1 > 0.02:
                break

        t2 = time.time()
        distance = ((t2 - t1) * 340 / 2) * 100
        print(distance)
        return distance

    def line_tracking_turn_type(self):
        """
        Indicates the type of turn required given current sensor values

        Returns
        -------
        * str
            - one of ['sharp_left_turn', 'sharp_right_turn',
                      'regular_left_turn', 'regular_right_turn',
                      'smooth_left', 'smooth_right',
                      'straight', 'no_line']
        """
        s1_dark = GPIO.input(PIN_TRACK_1) == GPIO.LOW
        s2_dark = GPIO.input(PIN_TRACK_2) == GPIO.LOW
        s3_dark = GPIO.input(PIN_TRACK_3) == GPIO.LOW
        s4_dark = GPIO.input(PIN_TRACK_4) == GPIO.LOW

        if s1_dark and (s3_dark and s4_dark):
            #   1    2    3    4
            # Dark XXXX Dark Dark
            # Dark XXXX Dark Lite
            # Dark XXXX Lite Dark
            # Requires a sharp left turn (line bends at right or acute angle)
            turn = 'sharp_left_turn'
        elif (s1_dark or s2_dark) and s4_dark:
            #   1    2    3    4
            # Dark Dark XXXX Dark
            # Lite Dark XXXX Dark
            # Dark Lite XXXX Dark
            # Requires a sharp right turn (line bends at right or acute angle)
            turn = 'sharp_right_turn'
        elif s1_dark:
            #   1    2    3    4
            # Dark XXXX XXXX XXXX
            # Requires a regular left turn (line bends at obtuse angle)
            turn = 'regular_left_turn'
        elif s4_dark:
            #   1    2    3    4
            # XXXX XXXX XXXX Dark
            # Requires a regular right turn (line bends at obtuse angle)
            turn = 'regular_right_turn'
        elif s2_dark and not s3_dark:
            #   1    2    3    4
            # XXXX Dark Lite XXXX
            # Requires a smooth curve to the left (car veers off to the right)
            turn = 'smooth_left'
        elif not s2_dark and s3_dark:
            #   1    2    3    4
            # XXXX Lite Dark XXXX
            # Requires a smooth curve to the right (car veers off to the left)
            turn = 'smooth_right'
        elif s2_dark and s3_dark:
            #   1    2    3    4
            # XXXX Dark Dark XXXX
            # Requires going straight
            turn = 'straight'
        else:
            #   1    2    3    4
            # Lite Lite Lite Lite
            # Requires maintaining the previous movement
            turn = 'no_line'

        print('Turn type = {}'.format(turn))
        return turn

    def demo_line_tracking(speed=50):
        """
        Demonstrates the line tracking mode using the line tracking sensor
        """
        time.sleep(2)
        car = Car()
        try:
            while True:
                turn = car.line_tracking_turn_type()
                if turn == 'straight':
                    car.run_forward(speed=speed)
                elif turn == 'smooth_left':
                    car.turn_left(speed=speed * 0.75)
                elif turn == 'smooth_right':
                    car.turn_right(speed=speed * 0.75)
                elif turn == 'regular_left_turn':
                    car.spin_left(speed=speed * 0.75)
                elif turn == 'regular_right_turn':
                    car.spin_right(speed=speed * 0.75)
                elif turn == 'sharp_left_turn':
                    car.spin_left(speed=speed)
                elif turn == 'sharp_right_turn':
                    car.spin_right(speed=speed)
        except KeyboardInterrupt:
            car.stop_completely()

    def demo_cruising(self):
        """
        Demonstrates a cruising car that avoids obstacles in a room

        * Use infrared sensors and ultrasonic sensor to gauge obstacles
        * Use LED lights to indicate running/turning decisions
        """
        try:
            while True:
                obstacle_status_from_infrared = self.obstacle_status_from_infrared()
                should_turn = True
                if obstacle_status_from_infrared == 'clear':
                    should_turn = False
                    obstacle_status_from_ultrasound = \
                        self.obstacle_status_from_ultrasound()
                    if obstacle_status_from_ultrasound == 'clear':
                        self.led_light('green')
                        self.run_forward(speed=10)
                    elif obstacle_status_from_ultrasound == 'approaching_obstacle':
                        self.led_light('yellow')
                        self.run_forward(speed=5)
                    else:
                        should_turn = True
                if should_turn:
                    self.run_reverse(duration=0.02)
                    if obstacle_status_from_infrared == 'only_right_blocked':
                        self.led_light('purple')
                        self.spin_left(duration=np.random.uniform(0.25, 1.0))
                    elif obstacle_status_from_infrared == 'only_left_blocked':
                        self.led_light('cyan')
                        self.spin_right(duration=random.uniform(0.25, 1.0))
                    else:
                        self.led_light('red')
                        self.spin_right(duration=random.uniform(0.25, 1.0))
        except KeyboardInterrupt:
            self.stop_completely()

    def obstacle_status_from_infrared(self):
        """
        Return obstacle status obtained by infrared sensors that
        are situated at the left front and right front of the Car.
        The infrared sensors are located on the lower deck, so they
        have a lower view than the ultrasonic sensor.

        Indicates blockage by obstacle < 20cm away.
        Depending on sensitivity of sensors, the distance of obstacles
        sometimes needs to be as short as 15cm for effective detection

        Returns
        -------
        * str
            - one of ['only_left_blocked', 'only_right_blocked',
                    'blocked', 'clear']
        """
        is_left_clear  = GPIO.input(PIN_INFRARED_LEFT)
        is_right_clear = GPIO.input(PIN_INFRARED_RIGHT)

        if is_left_clear and is_right_clear:
            status = 'clear'
        elif is_left_clear and not is_right_clear:
            status = 'only_right_blocked'
        elif not is_left_clear and is_right_clear:
            status = 'only_left_blocked'
        else:
            status = 'blocked'
        print('Infrared status = {}'.format(status))
        return status

    def obstacle_status_from_ultrasound(self, dir='center'):
        """
        Return obstacle status obtained by ultrasonic sensor that is
        situated in the front of the Car. The ultrasonic sensor is
        located in the upper deck so it has a higher view than the
        infrared sensors.

        Parameters
        ----------
        * dir : str
            - set the ultrasonic sensor to face a direction,
            one of ['center', 'left', 'right']. Default is 'center'

        Returns
        -------
        * str
            - 'blocked' if distance <= 20cm
            - 'approaching_obstacle' if distance is (20, 50]
            - 'clear' if distance > 50cm
        """

        self.turn_servo_ultrasonic(dir)
        distance = self.distance_from_obstacle()
        if distance <= 20:
            status = 'blocked'
        elif distance <= 50:
            status = 'approaching_obstacle'
        else:
            status = 'clear'
        print('Ultrasound status = {}'.format(status))
        return status

    def check_left_obstacle_with_sensor(self ,delay = 0):
        """
        利用小车左侧的红外对管传感器检测物体是否存在

        Parameters
        ----------
        * delay ：int
        读取稳定时间

        Returns
        -------
        * bool
            - High : 有障碍
            -Low   : 无障碍
        """
        have_obstacle = GPIO.input(PIN_AVOID_LEFT_SENSOR)
        time.sleep(delay)
        if have_obstacle :
            return NO_OBSTACLE
        else:
            return HAVE_OBSTACLE

    def check_right_obstacle_with_sensor(self ,delay = 0):
        """
        利用小车右侧的红外对管传感器检测物体是否存在

        Parameters
        ----------
        * delay ：int
        读取稳定时间
        -----------
        Returns
        -------
        * bool
            - High : 有障碍
            -Low   : 无障碍
        """
        have_obstacle = GPIO.input(PIN_AVOID_RIGHT_SENSOR)
        time.sleep(delay)

        if have_obstacle:
            return NO_OBSTACLE
        else:
            return HAVE_OBSTACLE

    def servo_front_rotate(self , pos):
        """
        *function:servo_front_roate
        功能：控制超声波的舵机进行旋转
        舵机：SG90 脉冲周期为20ms,脉宽0.5ms-2.5ms对应的角度-90到+90，对应的占空比为2.5%-12.5%
        Parameters
        *pos
        舵机旋转的角度：0 到 180 度
        ----------
        * none
        Returns
        -------
        None
        """
        for i in range(SERVO_TOTAL_STEP):
            self.__pwm_front_servo_pos.ChangeDutyCycle(2.5 + 10 * pos / 180)
            time.sleep(0.02)

        self.__pwm_front_servo_pos.ChangeDutyCycle(0)
        time.sleep(0.02)

    def servo_camera_rotate(self , pos):
        """
        *function:servo_camera_roate
        功能：调整控制相机的舵机进行旋转
        原理：舵机：SG90 脉冲周期为20ms,脉宽0.5ms-2.5ms对应的角度-90到+90，对应的占空比为2.5%-12.5%

        Parameters
        *pos
        舵机旋转的角度：0 到 180 度
        ----------
        Returns
        -------
        * None
        """
        for i in range(SERVO_TOTAL_STEP):
            self.__pwm_left_right_servo_pos.ChangeDutyCycle(2.5 + 10 * pos / 180)
            time.sleep(0.02)

        self.__pwm_left_right_servo_pos.ChangeDutyCycle(0)
        time.sleep(0.02)


    def servo_camera_rise_fall(self , pos):
        """
        *function:servo_camera_rise_fall
        功能：舵机让相机上升和下降
        舵机：SG90 脉冲周期为20ms,脉宽0.5ms-2.5ms对应的角度-90到+90，对应的占空比为2.5%-12.5%
        Parameters
        *pos
        舵机旋转的角度：0 到 180 度
        ----------
        Returns
        -------
        * None
        """
        for i in range(SERVO_TOTAL_STEP):
            self.__pwm_up_down_servo_pos.ChangeDutyCycle(2.5 + 10 * pos / 180)
            time.sleep(0.02)

        self.__pwm_up_down_servo_pos.ChangeDutyCycle(0)
        time.sleep(0.02)

    def function_registration(self):
        """
        *function:function_registration
        功能：用于对函数列表的注册，把函数名作为字段，映射到函数
        Parameters
        * None
        Returns
        -------
        * None
        """
        #舵机函数注册
        self.Function_List['servo_camera_rise_fall'] = self.servo_camera_rise_fall
        self.Function_List['servo_camera_rotate']    = self.servo_camera_rotate
        self.Function_List['servo_front_rotate']     = self.servo_front_rotate

        #灯的控制函数注册
        self.Function_List['turn_on_led'] = self.turn_on_led
        self.Function_List['trun_off_led'] = self.turn_off_led

        #运动控制函数注册
        self.Function_List['run_forward'] = self.run_forward
        self.Function_List['run_reverse'] = self.run_reverse
        self.Function_List['turn_left']   = self.turn_left
        self.Function_List['turn_right']  = self.turn_right
        self.Function_List['spin_left']   = self.spin_left
        self.Function_List['spin_right']  = self.spin_right

        self.Function_List['demo_cruising']= self.demo_cruising

        #超声波检测函数注册
        self.Function_List['check_right_obstacle_with_sensor']  = self.check_right_obstacle_with_sensor

        #红外对管检测函数注册
        self.Function_List['check_left_obstacle_with_sensor']  = self.check_left_obstacle_with_sensor

    def star_server(self, port):
        """
        *function:star_server
        功能：开辟一个线程用于网络服务
        Parameters
        * port：管道类型
        网络的IP 和 端口号，例如（（192.168.12.45），80）
        ————
        Returns
        -------
        * None
        """
        self.function_registration()

        self.Ip_Port = port
        self.serverThread = threading.Thread(None, target=self.net_call_function, args=(self.Function_List,))
        # tart the thread
        self.serverThread.start()

    def move_thread(self, func):
        """
        *function:move_thread
        功能：对运动函数的调用
        Parameters
        * func:dict
        函数列表
        ————
        Returns
        -------
        * None
        """
        print("move_thread:")

        for key in func:
            para = func[key]
            num = len(para)

            if num == ONE_PARA:
                self.Function_List[key](para[0])
            if num == TWO_PARA:
                self.Function_List[key](para[0], para[1])
        self.stop_all_wheels()

    def net_call_function(self, Function_List):
        """
        *function:star_server
        功能：时时网络连接
        Parameters：tupple类型
        * port：网络的IP
        ————
        Returns
        -------
        * None
        """
        print("net_call_function")

        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.server.bind(self.Ip_Port)
        self.server.listen(1)

        while True:
            time.sleep(0.5)
            conn,addr = self.server.accept()
            while True:
                try:
                    data     =  conn.recv(1024).decode('utf-8')
                    print((data))
                    strJson = eval(data)

                    process = strJson['function']
                    mode    = strJson['mode']

                    if mode == THREAD_CALL:
                        moveThread = threading.Thread(None, target=self.move_thread, args=(process,))
                        moveThread.start()
                        conn.send(bytes('res ok', encoding='utf8'))

                    else:
                        if mode == DERECT_CALL:
                            for key in process:
                                para = process[key]
                                num = len(para)

                                if num == ONE_PARA:
                                    self.Function_List[key](para[0])
                                if num == TWO_PARA:
                                    self.Function_List[key](para[0], para[1])
                            conn.send(bytes('res ok', encoding='utf8'))
                        else:
                            if mode == RETURN_CALL:
                                print('return call')
                                for key in process:
                                    para = process[key]
                                    num = len(para)

                                    if num == ONE_PARA:
                                        print('call one para')
                                        re = self.Function_List[key](para[0])
                                        print(re)
                                    if num == TWO_PARA:
                                        print('call two para')
                                        re = self.Function_List[key](para[0], para[1])
                                strRe = "%d"%(re)
                                print(strRe)
                                conn.send(bytes(strRe, encoding='utf8'))
                except:
                    print('close connect')
                    conn.close()
                    break


def main():
    test = Car()
    test.demo_cruising()
    test.star_server(('172.16.10.227', 12347))

if __name__ == "__main__":
    main()




    
    





    






      


  
  




