/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include <string.h>
/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
UART_HandleTypeDef huart3;

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART3_UART_Init(void);
int led_control(char which_led);
char UART_Decrypt_Command(const char *data);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART3_UART_Init();
  /* USER CODE BEGIN 2 */
  HAL_UART_Transmit(&huart3, (uint8_t *) "The STM is now online\r\n", 24, 100);
  uint8_t data;
  char buffer[50];
  int i = 0;
  int receiving = 0;
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
	  if (HAL_UART_Receive(&huart3, &data, 1, 100) == HAL_OK)
	      {

	          if (data == '#')
	          {
	              i = 0;
	              receiving = 1;
	          }
	          else if (receiving)
	          {
	              if (data == '\r' || data == '\n')
	              {
	                  buffer[i] = '\0';

	                  HAL_UART_Transmit(&huart3, (uint8_t *)"\r\nReceived: ", 12, 100);
	                  HAL_UART_Transmit(&huart3, (uint8_t *)buffer, strlen(buffer), 100);
	                  HAL_UART_Transmit(&huart3, (uint8_t *)"\r\n", 2, 100);

	                  if (i > 0)
	                  {
	                      led_control(UART_Decrypt_Command(buffer));
	                  }

	                  i = 0;
	                  receiving = 0;
	              }
	              else if (i < sizeof(buffer) - 1)
	              {
	                  buffer[i] = data;
	                  i++;
	              }
	              else
	              {
	                  i = 0;
	                  receiving = 0; //buffer overflow
	              }
	          }
	      }
    /* USER CODE END WHILE */
    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

char UART_Decrypt_Command(const char *data){
	//this decrypts command from terminal
	char which_led = '0';
	if(strstr(data, "MANIP GREEN") != NULL){
		which_led = '1';
	}
	else if(strstr(data, "MANIP ORANGE") != NULL){
		which_led = '2';
	}
	else if(strstr(data, "MANIP RED") != NULL){
		which_led = '3';
	}
	else if(strstr(data, "MANIP BLUE") != NULL){
		which_led = '4';
	}
	else if(strstr(data, "LED STATUS") != NULL){
		which_led = '5';
	}
	else if(strstr(data, "MANIP ALL ON") != NULL){
		which_led = '6';
	}
	else if(strstr(data, "MANIP ALL OFF") != NULL){
		which_led = '7';
	}
	else{
		which_led = '0';
	}
	return which_led;
}

int led_control(char which_led){
	// I decided to use strlen, so I created fragments of messages, which isn't necessary but I decided to use it anyway.
	char msg_led_green[] = " - LED Green";
	char msg_led_orange[] = " - LED Orange";
	char msg_led_red[] = " - LED Red";
	char msg_led_blue[] = " - LED Blue";
	char msg_all_leds[] = " - ALL LEDS ARE ";
	char msg_ON[] = " ON\r\n";
	char msg_OFF[] = " OFF\r\n";
	char msg_error[] = " u did something wong idk\r\n";
	// this switch case manipulates the state of leds
	// if when case is triggered the pin is SET then it will be RESET and wise-versa
	switch(which_led)
	{
	case '1':
		//green led
		if(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_12) == GPIO_PIN_RESET){
			HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12,GPIO_PIN_SET);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_green, strlen(msg_led_green), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_ON, strlen(msg_ON), 100);
			break;
		} else {
			HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12,GPIO_PIN_RESET);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_green, strlen(msg_led_green), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_OFF, strlen(msg_OFF), 100);
			break;
		}
	case '2':
		//orange led
		if(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_13) == GPIO_PIN_RESET){
			HAL_GPIO_WritePin(GPIOD, GPIO_PIN_13,GPIO_PIN_SET);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_orange, strlen(msg_led_orange), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_ON, strlen(msg_ON), 100);
			break;
		} else {
			HAL_GPIO_WritePin(GPIOD, GPIO_PIN_13,GPIO_PIN_RESET);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_orange, strlen(msg_led_orange), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_OFF, strlen(msg_OFF), 100);
			break;
		}
	case '3':
		//red led
		if(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_14) == GPIO_PIN_RESET){
			HAL_GPIO_WritePin(GPIOD, GPIO_PIN_14,GPIO_PIN_SET);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_red, strlen(msg_led_red), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_ON, strlen(msg_ON), 100);
			break;
		} else {
			HAL_GPIO_WritePin(GPIOD, GPIO_PIN_14,GPIO_PIN_RESET);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_red, strlen(msg_led_red), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_OFF, strlen(msg_OFF), 100);
			break;
		}
	case '4':
		//blue led
		if(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_15) == GPIO_PIN_RESET){
			HAL_GPIO_WritePin(GPIOD, GPIO_PIN_15,GPIO_PIN_SET);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_blue, strlen(msg_led_blue), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_ON, strlen(msg_ON), 100);
			break;
		} else {
			HAL_GPIO_WritePin(GPIOD, GPIO_PIN_15,GPIO_PIN_RESET);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_blue, strlen(msg_led_blue), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_OFF, strlen(msg_OFF), 100);
			break;
		}
	case '5':
		//this case  shows statuses of all leds, why not individually? idk why not all
		HAL_UART_Transmit(&huart3, (uint8_t *) "LED Statuses:\r\n", 15, 100);
		if(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_12) == GPIO_PIN_SET){
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_green, strlen(msg_led_green), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_ON, strlen(msg_ON), 100);
		} else {
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_green, strlen(msg_led_green), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_OFF, strlen(msg_OFF), 100);
		}
		if(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_13) == GPIO_PIN_SET){
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_orange, strlen(msg_led_orange), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_ON, strlen(msg_ON), 100);
		} else {
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_orange, strlen(msg_led_orange), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_OFF, strlen(msg_OFF), 100);
		}
		if(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_14) == GPIO_PIN_SET){
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_red, strlen(msg_led_red), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_ON, strlen(msg_ON), 100);
		} else {
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_red, strlen(msg_led_red), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_OFF, strlen(msg_OFF), 100);
		}
		if(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_15) == GPIO_PIN_SET){
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_blue, strlen(msg_led_blue), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_ON, strlen(msg_ON), 100);
		} else {
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_led_blue, strlen(msg_led_blue), 100);
			HAL_UART_Transmit(&huart3, (uint8_t *) msg_OFF, strlen(msg_OFF), 100);
		}
		break;
	case '6':
		//all leds on
		HAL_UART_Transmit(&huart3, (uint8_t *) msg_all_leds, strlen(msg_all_leds), 100);
		HAL_UART_Transmit(&huart3, (uint8_t *) msg_ON, strlen(msg_ON), 100);
		HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12 | GPIO_PIN_13 | GPIO_PIN_14 | GPIO_PIN_15, GPIO_PIN_SET);
		break;
	case '7':
		//all leds off
		HAL_UART_Transmit(&huart3, (uint8_t *) msg_all_leds, strlen(msg_all_leds), 100);
		HAL_UART_Transmit(&huart3, (uint8_t *) msg_OFF, strlen(msg_OFF), 100);
		HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12 | GPIO_PIN_13 | GPIO_PIN_14 | GPIO_PIN_15, GPIO_PIN_RESET);
		break;
	default:
		HAL_UART_Transmit(&huart3, (uint8_t *) msg_error, strlen(msg_error), 100);
		break;
	}
	return 0;
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART3 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART3_UART_Init(void)
{

  /* USER CODE BEGIN USART3_Init 0 */

  /* USER CODE END USART3_Init 0 */

  /* USER CODE BEGIN USART3_Init 1 */

  /* USER CODE END USART3_Init 1 */
  huart3.Instance = USART3;
  huart3.Init.BaudRate = 19200;
  huart3.Init.WordLength = UART_WORDLENGTH_8B;
  huart3.Init.StopBits = UART_STOPBITS_1;
  huart3.Init.Parity = UART_PARITY_NONE;
  huart3.Init.Mode = UART_MODE_TX_RX;
  huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart3.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart3) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART3_Init 2 */

  /* USER CODE END USART3_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOD_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12|GPIO_PIN_13|GPIO_PIN_14|GPIO_PIN_15, GPIO_PIN_RESET);

  /*Configure GPIO pins : PD12 PD13 PD14 PD15 */
  GPIO_InitStruct.Pin = GPIO_PIN_12|GPIO_PIN_13|GPIO_PIN_14|GPIO_PIN_15;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
