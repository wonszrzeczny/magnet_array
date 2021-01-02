#include <Tlv493d.h>

// Tlv493d Opject
Tlv493d Tlv493dMagnetic3DSensor = Tlv493d();
String input="";
void setup() {
  Serial.begin(9600);
  while(!Serial);
  Tlv493dMagnetic3DSensor.begin();
}

  
void loop(){
  

   while (Serial.available()) {
    delay(1);  //delay to allow buffer to fill
    if (Serial.available() >0) {
      char c = Serial.read();  
      input += c; 
    }
  }
  
  if (input.length() >0) {
  Tlv493dMagnetic3DSensor.updateData();
  Serial.print(Tlv493dMagnetic3DSensor.getX());
  Serial.print(" ");
  Serial.print(Tlv493dMagnetic3DSensor.getY());
  Serial.print(" ");
  Serial.println(Tlv493dMagnetic3DSensor.getZ());
  input="";

  }
}
