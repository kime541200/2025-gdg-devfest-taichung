// =================== 完整通訊版本 v2 (增加查詢功能) ===================

const int ledPins[] = {9, 10, 11};
const int NUM_LEDS = sizeof(ledPins) / sizeof(ledPins[0]); // 更彈性的寫法，自動計算 LED 數量

int brightness[NUM_LEDS] = {0}; // C++ 會自動將剩餘元素初始化為 0

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(ledPins[i], OUTPUT);
  }
  while (!Serial) { ; }
  Serial.println("Arduino Ready.");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    processCommand(command);
  }
}

void processCommand(String command) {
  if (command.startsWith("<") && command.endsWith(">")) {
    // (這部分和之前一樣，省略註解)
    command = command.substring(1, command.length() - 1);
    int commaIndex = command.indexOf(',');
    if (commaIndex > 0) {
      String indexStr = command.substring(0, commaIndex);
      String valueStr = command.substring(commaIndex + 1);
      int ledIndex = indexStr.toInt();
      int value = valueStr.toInt();
      if (ledIndex >= 0 && ledIndex < NUM_LEDS) {
        value = constrain(value, 0, 255);
        analogWrite(ledPins[ledIndex], value);
        brightness[ledIndex] = value;
      }
    }
  } 
  else if (command == "s") {
    reportStatus();
  }
  // =================== 新增的程式碼 ===================
  else if (command == "i") {
    reportInfo(); // 當收到 'i' 指令時，呼叫 reportInfo 函數
  }
  // ======================================================
}

void reportStatus() {
  String status = "S,";
  for (int i = 0; i < NUM_LEDS; i++) {
    status += String(brightness[i]);
    if (i < NUM_LEDS - 1) {
      status += ",";
    }
  }
  Serial.println(status);
}

// =================== 新增的函數 ===================
void reportInfo() {
  // 回傳 'I,' 加上 LED 的總數
  Serial.print("I,");
  Serial.println(NUM_LEDS);
}
// ===============================================