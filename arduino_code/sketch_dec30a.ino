#define EN        8 



int dirs[3] = {5, 6, 7};
int steps[3] = {2, 3, 4};
String input, command;


//Direction pin
#define X_DIR     5 
#define Y_DIR     6
#define Z_DIR     7

//Step pin
#define X_STP     2
#define Y_STP     3 
#define Z_STP     4 

String wtf = "";
//DRV8825
int delayTime=100;
long stps= 288000;
long pos[3] = {0,0,0};

void move(boolean dir, int dirPin, int stepperPin, long steps)

{
  digitalWrite(dirPin, dir);
  delay(10);
  for (long i = 0L; i < steps; i++) {
    digitalWrite(stepperPin, HIGH);
    delayMicroseconds(1); 
    digitalWrite(stepperPin, LOW);
    delayMicroseconds(30); 
  }
}

void step(int index, long dist){
  move(dist > 0, dirs[index], steps[index], abs(dist));
  pos[index] += dist;
}

String getValue(String data, char separator, int index)
{
    int found = 0;
    int strIndex[] = { 0, -1 };
    int maxIndex = data.length() - 1 - (data[data.length()-1]==char('\n'));
    for (int i = 0; i <= maxIndex && found <= index; i++) {
        if (data.charAt(i) == separator || i == maxIndex) {
            found++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i+1 : i;
        }
    }
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}
long parse_long(String data){
  if(data[0]=='-'){
    return -data.substring(1, data.length()).toInt();
    } else { return data.toInt();}
}

void setup(){
  Serial.begin(9600);
  Serial.setTimeout(100);
  pinMode(X_DIR, OUTPUT); pinMode(X_STP, OUTPUT);
  pinMode(Y_DIR, OUTPUT); pinMode(Y_STP, OUTPUT);
  pinMode(Z_DIR, OUTPUT); pinMode(Z_STP, OUTPUT);
  pinMode(EN, OUTPUT);
  digitalWrite(EN, LOW);
}



void loop(){
   while (Serial.available()) {
    delay(10);  //delay to allow buffer to fill
    if (Serial.available() >0) {
      char c = Serial.read();  
      input += c; 
    }
  }


  //handling input
  if (input.length() >0) {

    //moving magnets format: move dx dy dz db
    if(getValue(input, ' ', 0) == "mov" or getValue(input, ' ', 0) == "move"){
      for(int index = 0; index  < 3; index+=1){
        long val = parse_long(getValue(input,' ', index+1));
        step(index, val);
      } 
        }
    //position query
    if(getValue(input, ' ', 0) == "pos"){
      String output = "";
      for(int i=0; i < 3; i++){
        output+=String(pos[i]) + " ";
      }
      Serial.println(output);
    }
    

    //turning on and off between uses since it heats up and we don't want to turn off the arduino, since it has the positions
    
    if(getValue(input, ' ', 0) == "off"){
    digitalWrite(EN, HIGH);
    }
    if(getValue(input, ' ', 0) == "on"){
    digitalWrite(EN, LOW);
    }
  
  }
  delay(10);
  input = "";
}