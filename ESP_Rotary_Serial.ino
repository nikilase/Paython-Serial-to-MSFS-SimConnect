// Library available in Arduino Library tool.
// Only compatible with ESP32!
#include <ESP32Encoder.h>


// Encoder objects
ESP32Encoder vs, alt, crs, hdg, baro;


// Pin definition of the rotary encoders
// A is A or "CLK" Pin, B is B or "DT" Pin and Btn is the button
// Prefix denotes the "function" of the encoder like alt for altitude
enum PinAssignments {
  
  vsA     = 23,   
  vsB     = 22,   
  vsBtn   = 21,    
  
  altA    = 19,   
  altB    = 18,   
  altBtn  = 5,   

  crsA    = 17,   
  crsB    = 16,   
  crsBtn  = 15,    
  
  hdgA    = 34,   
  hdgB    = 35,   
  hdgBtn  = 32,    

  baroA   = 33,   
  baroB   = 25,   
  baroBtn = 26,  
};


// Current and last state of the button
int vsBtnState, 
altBtnState, 
crsBtnState, 
hdgBtnState, 
baroBtnState;
           
int vsBtnStateOld = LOW, 
altBtnStateOld = LOW, 
crsBtnStateOld = LOW, 
hdgBtnStateOld = LOW, 
baroBtnStateOld = LOW;   


// Debounce delay and thelast time each pin was toggled
unsigned long debounceDelay = 50; 
unsigned long vsDebounceTime = 0, 
altDebounceTime = 0, 
crsDebounceTime = 0, 
hdgDebounceTime = 0,
baroDebounceTime = 0;


void setup() {
  Serial.begin(115200);
  
  // Set Pin Mode of buttons
  pinMode(vsBtn, INPUT_PULLUP);
  pinMode(altBtn, INPUT_PULLUP);
  pinMode(crsBtn, INPUT_PULLUP);
  pinMode(hdgBtn, INPUT_PULLUP);
  pinMode(baroBtn, INPUT_PULLUP);

  // Encoder uses internal Pullup Resistors
  ESP32Encoder::useInternalWeakPullResistors=UP;

  // Attach Pins to the encoders and reset counter
  vs.attachHalfQuad(vsA,vsB);
  alt.attachHalfQuad(altA,altB);
  crs.attachHalfQuad(crsA,crsB);
  hdg.attachHalfQuad(hdgA,hdgB);
  baro.attachHalfQuad(baroA,baroB);
  
  vs.setCount(0);
  alt.setCount(0);
  crs.setCount(0);
  hdg.setCount(0);
  baro.setCount(0);  
}


void loop() {
  // Get update of encoders
  encode32(vs, "vs");
  encode32(alt, "alt");
  encode32(crs, "crs");
  encode32(hdg, "hdg");
  encode32(baro, "baro");

  // Get debounced value of rotary encoder
  if(button(altBtn, &altBtnState, &altBtnStateOld, &altDebounceTime, debounceDelay, "alt")){
    Serial.println("alt_sync");
  }
  if(button(vsBtn, &vsBtnState, &vsBtnStateOld, &vsDebounceTime, debounceDelay, "vs")){
    Serial.println("vs_sync");
  }
  if(button(crsBtn, &crsBtnState, &crsBtnStateOld, &crsDebounceTime, debounceDelay, "crs")){
    Serial.println("crs_sync");
  }
  if(button(hdgBtn, &hdgBtnState, &hdgBtnStateOld, &hdgDebounceTime, debounceDelay, "hdg")){
    Serial.println("hdg_sync");
  }
  if(button(baroBtn, &baroBtnState, &baroBtnStateOld, &baroDebounceTime, debounceDelay, "baro")){
    Serial.println("baro_sync");
  }
  
  delay(10);
}

void encode32(ESP32Encoder& encoder, String type){
  int cnt = encoder.getCount();
  
  if(cnt > 1 && (cnt % 2 == 0)) {
    Serial.println(type + "-");
    cnt = cnt - 2;
    encoder.setCount(cnt);
  }
  if(cnt < -1 && (cnt % 2 == 0)) {
    Serial.println(type + "+");
    cnt = cnt + 2;
    encoder.setCount(cnt);
  }
  return;
}

// Debounce function from the Arduino Docs
boolean button(int btn, int *btnState, int *btnStateOld, unsigned long *lastDebounce, unsigned long debounceDelay, String type) {
  int reading = digitalRead(btn);
  // If the switch changed, due to noise or pressing:
  if (reading != *btnStateOld) {
    // reset the debouncing timer
    *lastDebounce = millis();
  }

  if ((millis() - *lastDebounce) > debounceDelay) {

    // if the button state has changed:
    if (reading != *btnState) {
      *btnState = reading;
     
      // only toggle the LED if the new button state is HIGH
      if (*btnState == 1) {
        return true;
        //Serial.println(type + "_sync");
      }
    }
  }
  // save the reading. Next time through the loop, it'll be the lastButtonState:
  *btnStateOld = reading;
  return false;
}
