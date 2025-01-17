/******************************************************************************************
 * FileName      : RobotArm.ino
 * Description   : When a pin input is received, perform the specified movement action
 * Author        : Habeen Lee
 * Last Modified : 2024.08.13
 ******************************************************************************************/
#include <open_manipulator_libs.h>
#include "Arduino.h"

#define signal 5

OpenManipulator open_manipulator;
double control_time = 0.010;  // default control frequency (100Hz)
double present_time = 0.0;
double previous_time = 0.0;
bool platform_state = true;
bool start_motion_flag = false;
bool stop_motion_flag = false;
bool teaching_mode_flag = false;
uint8_t motion_cnt[] = {0};
uint8_t motion_index = 0;
uint8_t motion_number = 0;

std::vector<JointValue> present_position;
std::vector<JointValue> gripper_position;
std::vector<JointValue> saved_teaching_pose;

bool virtual_button1 = false;

void setup()
{
  Serial.begin(9600);
  while (!Serial);  // Wait until Serial is Opened
  
  pinMode(signal, INPUT);  // D2 핀을 입력 모드로 설정

  open_manipulator.setOpenManipulatorCustomJointId(11, 12, 13, 14, 15); // ID 11, 12, 13, 14, 15 is default
  open_manipulator.initOpenManipulator(platform_state);
  Serial.println("OpenManipulator Init Begin");

  initDemo();
  
  Serial.println("Press [SW1] to start programmed motion. Press [SW2] to start teaching mode.");
  
  digitalWrite(BDPIN_LED_USER_1, HIGH);
}

void loop()
{

  int input = digitalRead(signal);  // D2 핀의 신호 읽기
  if (input == HIGH) {
    virtual_button1 = true;
  } else {
    virtual_button1 = false;
  }

  if (teaching_mode_flag)
  {
    open_manipulator.disableAllActuator();
    delay_ms(1000);
    Serial.println("Press [SW2] to append Current Pose. Press [SW1] to finish appending pose and play taught pose");

    while (true)
    {
      digitalWrite(BDPIN_LED_USER_2, LOW);
      if (digitalRead(BDPIN_PUSH_SW_2))
      {
        // Append(Teach) the current Pose to the present_position data
        uint8_t pos_vector_index = motion_index;
        present_position = open_manipulator.receiveAllJointActuatorValue();
        gripper_position = open_manipulator.receiveAllToolActuatorValue();
        for (uint8_t joint_index = 0; joint_index < 4; joint_index++)
        {
          saved_teaching_pose.push_back(present_position.at(joint_index));
        }
        saved_teaching_pose.push_back(gripper_position.at(0));

        // Display saved Pose Joint angles in Radian
        Serial.print("[Pose ");
        Serial.print(motion_index / 5 + 1);
        Serial.print("] : ");
        Serial.print(saved_teaching_pose[pos_vector_index++].position, 3);
        Serial.print(", ");
        Serial.print(saved_teaching_pose[pos_vector_index++].position, 3);
        Serial.print(", ");
        Serial.print(saved_teaching_pose[pos_vector_index++].position, 3);
        Serial.print(", ");
        Serial.print(saved_teaching_pose[pos_vector_index++].position, 3);
        Serial.print(", ");
        Serial.println(saved_teaching_pose[pos_vector_index++].position, 3);
        motion_index = motion_index + 5;
        break;
      }
      if (digitalRead(BDPIN_PUSH_SW_1) || virtual_button1)
      {
        digitalWrite(BDPIN_LED_USER_3, LOW);
        teaching_mode_flag = false;

        // Display the list of saved(taught) Pose
        for (uint8_t index = 0; index < motion_index; index++)
        {
          if (index % 5 == 0)
          {
            Serial.println();
          }
          else
          {
            Serial.print(", ");
          }
          Serial.print(saved_teaching_pose[index].position, 3);
        }

        warning();
        break;
      }
    }
    digitalWrite(BDPIN_LED_USER_2, HIGH);
  }
  else
  {
    present_time = millis() / 1000.0;

    // Trajectory following movement occurs here
    if (present_time - previous_time >= control_time)
    {
      open_manipulator.processOpenManipulator(millis() / 1000.0);
      previous_time = millis() / 1000.0;
    }

    // Read the next Pose to move
    if (!saved_teaching_pose.empty())
    {
      runTeachingMotion(&open_manipulator);
    }
    else
    {
      runDemo(&open_manipulator);
    }
  }
}

// Output warning before starting motion
void warning()
{
  Serial.println();
  Serial.println("WARNING!!! OpenMANIPULATOR-X operates in 5 seconds.");
  delay_ms(1000);
  Serial.println("WARNING!!! OpenMANIPULATOR-X operates in 4 seconds.");
  delay_ms(1000);
  Serial.println("WARNING!!! OpenMANIPULATOR-X operates in 3 seconds.");
  delay_ms(1000);
  Serial.println("WARNING!!! OpenMANIPULATOR-X operates in 2 seconds.");
  delay_ms(1000);
  Serial.println("WARNING!!! OpenMANIPULATOR-X operates in 1 seconds.");
  open_manipulator.receiveAllJointActuatorValue();
  open_manipulator.receiveAllToolActuatorValue();
  open_manipulator.enableAllActuator();
  delay_ms(1000);
}

// Move in Joint Space 
void moveJS(OpenManipulator *open_manipulator, double j1, double j2, double j3, double j4, double gripper_pos, double time)
{
  static std::vector <double> target_angle;
  target_angle.clear();
  target_angle.push_back(j1);
  target_angle.push_back(j2);
  target_angle.push_back(j3);
  target_angle.push_back(j4);
  open_manipulator->makeJointTrajectory(target_angle, time);
  open_manipulator->makeToolTrajectory("gripper", gripper_pos);
}

/*****************************************************************************
** Initialize Demo
*****************************************************************************/
void initDemo()
{
  start_motion_flag = false;
  motion_cnt[0] = 0;

  pinMode(BDPIN_PUSH_SW_1, INPUT);
  pinMode(BDPIN_PUSH_SW_2, INPUT);
  pinMode(BDPIN_GPIO_1, OUTPUT);
  digitalWrite(BDPIN_GPIO_1, LOW);
  Serial.println("OpenManipulator Init Completed");
}

void runDemo(OpenManipulator *open_manipulator)
{
  if (!start_motion_flag && !stop_motion_flag)
  {
    startMotion();
  }
  if (!start_motion_flag && stop_motion_flag)  // Restart DEMO
  {
    if (digitalRead(BDPIN_PUSH_SW_1) || virtual_button1)
    {
      startMotion();
    }
  }
  if (digitalRead(BDPIN_PUSH_SW_2) && !stop_motion_flag)  // Stop DEMO
  {
    stopMotion(open_manipulator);
  }

  if (open_manipulator->getMovingState())
  {
    return;
  }
  else
  {
    if (start_motion_flag)
    {
      switch (motion_cnt[0])
      {
        case 0:
          moveJS(open_manipulator, 0.014, -0.012, -0.011, 0.002, 0.01, 2.0);
          Serial.println("CASE 0");
          motion_cnt[0]++;
          break;
        case 1:
          moveJS(open_manipulator, 0.015, 0.425, 1.009, -1.249, 0.01, 2.0);
          Serial.println("CASE 1");
          motion_cnt[0]++;
          break;
        case 2:
          moveJS(open_manipulator, 0.040, 0.425, 1.009, -1.249, -0.003, 2.0);
          Serial.println("CASE 2");
          motion_cnt[0]++;
          break;
        case 3:
          moveJS(open_manipulator, -0.043, -0.244, 0.198, 0.081, -0.003, 2.0);
          Serial.println("CASE 3");
          motion_cnt[0]++;
          break;
        case 4:
          moveJS(open_manipulator, 1.615, -0.242, 0.155, 0.094, -0.003, 2.0);
          motion_cnt[0]++;
          break;
        case 5:
          moveJS(open_manipulator, 1.606, 0.749, 0.977, -1.730, -0.003, 2.0);
          motion_cnt[0]++;
          break;
        case 6:
          moveJS(open_manipulator, 1.608, 0.749, 0.977, -1.730, 0.01, 2.0);
          motion_cnt[0]++;
          break;
        case 7:
          moveJS(open_manipulator, 1.545, 0.083, -0.238, 0.009, 0.01, 2.0);
          motion_cnt[0]++;
          break;
        case 8:
          moveJS(open_manipulator, 1.545, 0.083, -0.238, 0.009, 0.01, 2.0);
          motion_cnt[0] = 0;
          stopMotion(open_manipulator); // 모션이 끝나면 멈추기
          virtual_button1 = false;
          break;
        default:
          motion_cnt[0] = 0;
          break;
      }
    }
  }
}
/*****************************************************************************
** Play Teaching Motion
*****************************************************************************/
void runTeachingMotion(OpenManipulator *open_manipulator)
{
  if (!start_motion_flag && !stop_motion_flag) // Start Teach Motion
  {
    startMotion();
  }
  if (!start_motion_flag && stop_motion_flag)  // Restart Teach Motion
  {
    if (digitalRead(BDPIN_PUSH_SW_1) || virtual_button1)
    {
      startMotion();
    }
  }
  if (digitalRead(BDPIN_PUSH_SW_2) && !stop_motion_flag)  // Stop Teach Motion
  {
    stopMotion(open_manipulator);
    digitalWrite(BDPIN_LED_USER_1, HIGH); // Turn off USER1 LED
    digitalWrite(BDPIN_LED_USER_2, HIGH); // Turn off USER2 LED
    digitalWrite(BDPIN_LED_USER_3, HIGH); // Turn off USER3 LED
    digitalWrite(BDPIN_LED_USER_4, HIGH); // Turn off USER4 LED
  }

  if (open_manipulator->getMovingState()) // Check if OpenMANIPULATOR is moving along the trajectory
  {
    // If OpenMANIPULATOR is still moving along the trajectory, then do not get the next Pose and return to main loop
    // Digital Output HIGH(3.3V) on OpenCR GPIO pin #3 (http://emanual.robotis.com/docs/en/parts/controller/opencr10/#gpio)
    digitalWrite(BDPIN_GPIO_1, HIGH);
    return;
  }
  else
  {
    // Digital Output LOW(0V) on OpenCR GPIO pin #3 (http://emanual.robotis.com/docs/en/parts/controller/opencr10/#gpio)
    digitalWrite(BDPIN_GPIO_1, LOW);
    if (start_motion_flag)
    {
      if (motion_cnt[0] < motion_index)
      {
        uint8_t joint1_index = motion_cnt[0]++;
        uint8_t joint2_index = motion_cnt[0]++;
        uint8_t joint3_index = motion_cnt[0]++;
        uint8_t joint4_index = motion_cnt[0]++;
        uint8_t gripper_index = motion_cnt[0]++;

        // Play each motion during 3.0 seconds
        moveJS(open_manipulator, saved_teaching_pose[joint1_index].position, saved_teaching_pose[joint2_index].position, saved_teaching_pose[joint3_index].position, saved_teaching_pose[joint4_index].position, saved_teaching_pose[gripper_index].position, 3.0);
      }
      else
      {
        motion_cnt[0] = 0;
        stopMotion(open_manipulator); // 티칭 모션이 끝나면 멈추기
      }
    }
  }
}

/*****************************************************************************
** Start Motion
*****************************************************************************/
void startMotion()
{
  Serial.println("Press [SW2] to Stop Motion");
  // Start the motion
  start_motion_flag = true;
  stop_motion_flag = false;

  motion_cnt[0] = 0;
}

/*****************************************************************************
** Stop Motion
*****************************************************************************/
void stopMotion(OpenManipulator *open_manipulator)
{
  Serial.println("Press [SW1] to Start Motion");
  // Stop the motion
  start_motion_flag = false;
  stop_motion_flag = true;

  // Go to the Init Pose(Right angle pose).
  moveJS(open_manipulator, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0);
  motion_cnt[0] = 0;
}

//=========================================================================================
//
// SW_Bootcamp I5
//
//=========================================================================================
