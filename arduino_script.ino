const int SAMPLE_RATE = 1000;
const int ADC_PIN = A0;

void setup(){
    Serial.begin(115200);

    analogReadResolution(10);
}


void loop() {
    static unsigned long lastSampleTime = 0;
    unsigned long currentTime = micros();
    
    if (currentTime - lastSampleTime >= 1000000 / SAMPLE_RATE) {
      lastSampleTime = currentTime;
      
      int sample = analogRead(ADC_PIN);
      
      Serial.println(sample);
    }
  }