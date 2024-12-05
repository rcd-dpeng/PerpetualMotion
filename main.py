import os

#os.environ['DISPLAY'] = ":0.0"
#os.environ['KIVY_WINDOW'] = 'egl_rpi'

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock

from pidev.MixPanel import MixPanel
from pidev.kivy.PassCodeScreen import PassCodeScreen
from pidev.kivy.PauseScreen import PauseScreen
from pidev.kivy import DPEAButton
from pidev.kivy import ImageButton
from pidev.kivy.selfupdatinglabel import SelfUpdatingLabel
from pidev.Joystick import Joystick

from datetime import datetime

from dpeaDPi.DPiComputer import DPiComputer
from dpeaDPi.DPiStepper import *
from time import sleep

time = datetime

joy = Joystick(0, True)

MIXPANEL_TOKEN = "x"
MIXPANEL = MixPanel("Project Name", MIXPANEL_TOKEN)

SCREEN_MANAGER = ScreenManager()
MAIN_SCREEN_NAME = 'main'
ADMIN_SCREEN_NAME = 'admin'


class ProjectNameGUI(App):
    """
    Class to handle running the GUI Application
    """

    def build(self):
        """
        Build the application
        :return: Kivy Screen Manager instance
        """
        return SCREEN_MANAGER


Window.clearcolor = (1, 1, 1, 1)  # White


class MainScreen(Screen):
    """
    Class to handle the main screen and its associated touch events
    """

    def pressed(self):
        """
        Function called on button touch event for button with id: testButton
        :return: None
        """
        print("Callback from MainScreen.pressed()")

    def admin_action(self):
        """
        Hidden admin button touch event. Transitions to passCodeScreen.
        This method is called from pidev/kivy/PassCodeScreen.kv
        :return: None
        """
        SCREEN_MANAGER.current = 'passCode'

    def update_inputs(self, dt):
        xval = joy.get_axis('x')
        yval = joy.get_axis('y')
        jl = self.ids['joy_label']
        jl.text = "(" + str(round(xval, 3)) + ", " + str(round(yval, 3)) + ")"
        jl.center_x = self.width * 0.5 + xval * self.width * 0.5
        jl.center_y = self.height * 0.5 - yval * self.height * 0.5
        if joy.get_button_state(0) == True:
            jl.color = (1, 0, 0, 1)
        else:
            jl.color = (1, 1, 1, 1)

        # Limit Switch
        limitSwitchPressed = not dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0)
        limitSwitchLabel = self.ids['limitSwitchLabel']
        limitSwitchLabel.color = (1, 0, 0, 1) if limitSwitchPressed else (1, 1, 1, 1)
        limitSwitchLabel.text = "Limit Switch Closed" if limitSwitchPressed else "Limit Switch Open"

        servo_number = 0
        if limitSwitchPressed:
            for i in range(90, 180):
                dpiComputer.writeServo(servo_number, i)
                sleep(20 / (180-90)) # Seconds / steps
        else:
            dpiComputer.writeServo(servo_number, 90)


    def toggleMotor(self):
        global stepperMotorInit
        if(not stepperMotorInit):
            if dpiStepper.initialize() != True:
                print("Unable to connect to stepper motor.")
                return
            else:
                stepperMotorInit = True
        global stepperMotorEnabled

        stepperMotorEnabled = not stepperMotorEnabled
        dpiStepper.enableMotors(stepperMotorEnabled)

        toggleButton = self.ids['toggleMotorButton']
        toggleButton.color = (0, 1, 0, 1) if stepperMotorEnabled else (1, 0, 0, 1)

    def toggleMotorDirection(self):
        global stepperMotorDirection
        stepperMotorDirection = 0 - stepperMotorDirection

        toggleDirectionButton = self.ids['toggleMotorDirection']
        toggleDirectionButton.text = "Positive" if stepperMotorDirection > 0 else "Negative"

    def updatePosLabel(self):
        global stepperNum
        cPosSteps = dpiStepper.getCurrentPositionInSteps(stepperNum)

        posLabel = self.ids['motorPositionLabel']
        posLabel.text = "Last Position: " + str(cPosSteps)

    def setSpeedValues(self):
        dpiStepper.setAccelerationInMillimetersPerSecondPerSecond(0, 15)
        dpiStepper.setSpeedInMillimetersPerSecond(0, 75)

    def getPushyThingyBackToHome(self):
        dpiStepper.moveToHomeInMillimeters(0, 1, 75, 950)

    def openGate(self):
        dpiComputer.writeServo(1, 90)

    def closeGate(self):
        dpiComputer.writeServo(1, 0)

    def checkIfBallReachedSensor(self, num):
        return True if dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0 if num == 0 else dpiComputer.IN_CONNECTOR__IN_1) == 0 else False

    def getDaBallUpDaRamp(self):
        dpiStepper.moveToRelativePositionInMillimeters(0, -925, False)

    def startMovinDaBrokenStairs(self):
        dpiComputer.writeServo(0, 0)

    def run(self): # Assume ball starts behind servo gate that is closed
        global stepperMotorInit

        while(stepperMotorInit != True):
            initAttempt = dpiStepper.initialize()
            print(initAttempt)
            stepperMotorInit = initAttempt
            if(initAttempt):
                break

        while(True):
            self.getPushyThingyBackToHome()

            self.setSpeedValues()

            self.openGate()

            ballReachedSensor0 = False
            while(not ballReachedSensor0):
                ballReachedSensor0 = self.checkIfBallReachedSensor(0)

            self.setSpeedValues()

            self.closeGate()

            self.getDaBallUpDaRamp()

            ballReachedSensor1 = False
            while(not ballReachedSensor1):
                ballReachedSensor1 = self.checkIfBallReachedSensor(1)

            self.startMovinDaBrokenStairs()

            self.getPushyThingyBackToHome()

    def stop(self):
        dpiStepper.decelerateToAStop(0)
        dpiStepper.enableMotors(False)
        dpiComputer.writeServo(0, 90)
        dpiComputer.writeServo(1, 0)


class AdminScreen(Screen):
    """
    Class to handle the AdminScreen and its functionality
    """

    def __init__(self, **kwargs):
        """
        Load the AdminScreen.kv file. Set the necessary names of the screens for the PassCodeScreen to transition to.
        Lastly super Screen's __init__
        :param kwargs: Normal kivy.uix.screenmanager.Screen attributes
        """
        Builder.load_file('AdminScreen.kv')

        PassCodeScreen.set_admin_events_screen(ADMIN_SCREEN_NAME)  # Specify screen name to transition to after correct password
        PassCodeScreen.set_transition_back_screen(MAIN_SCREEN_NAME)  # set screen name to transition to if "Back to Game is pressed"

        super(AdminScreen, self).__init__(**kwargs)

    @staticmethod
    def transition_back():
        """
        Transition back to the main screen
        :return:
        """
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    @staticmethod
    def shutdown():
        """
        Shutdown the system. This should free all steppers and do any cleanup necessary
        :return: None
        """
        os.system("sudo shutdown now")

    @staticmethod
    def exit_program():
        """
        Quit the program. This should free all steppers and do any cleanup necessary
        :return: None
        """
        quit()


"""
Widget additions
"""

Builder.load_file('main.kv')
mainS = MainScreen(name=MAIN_SCREEN_NAME)
SCREEN_MANAGER.add_widget(mainS)
SCREEN_MANAGER.add_widget(PassCodeScreen(name='passCode'))
SCREEN_MANAGER.add_widget(PauseScreen(name='pauseScene'))
SCREEN_MANAGER.add_widget(AdminScreen(name=ADMIN_SCREEN_NAME))

"""
MixPanel
"""


def send_event(event_name):
    """
    Send an event to MixPanel without properties
    :param event_name: Name of the event
    :return: None
    """
    global MIXPANEL

    MIXPANEL.set_event_name(event_name)
    MIXPANEL.send_event()

joyClock = Clock.schedule_interval(mainS.update_inputs, 0.1)

dpiStepper = DPiStepper()
dpiStepper.setBoardNumber(0)
global stepperMotorInit
stepperMotorInit = False
if dpiStepper.initialize() != True:
    print("Communication with the DPiStepper board failed.")
else:
    stepperMotorInit = True
global stepperMotorEnabled
stepperMotorEnabled = False

global stepperMotorDirection
stepperMotorDirection = 1 # 1 for positive, -1 for negative

global stepperNum
stepperNum = 0

microstepping = 32
dpiStepper.setMicrostepping(microstepping)

global dpiComputer
dpiComputer = DPiComputer()

dpiComputer.initialize()

if __name__ == "__main__":
    # send_event("Project Initialized")
    # Window.fullscreen = 'auto'
    ProjectNameGUI().run()
