#define EN        8 


String input, command;


//Direction pin
#define X_DIR     5 
#define Y_DIR     6
#define Z_DIR     7
#define W_DIR     13

//Step pin
#define X_STP     2
#define Y_STP     3 
#define Z_STP     4 
#define W_STP     12


int dirs[4] = {X_DIR, Y_DIR, Z_DIR, W_DIR};
int steps[4] = {X_STP, Y_STP, Z_STP, W_STP};

//DRV8825
int delayTime=100; // unused
long stps= 18000;
long pos[4] = {0,0,0, 0};

void move(boolean dir, int dirPin, int stepperPin, long steps)

{
  digitalWrite(dirPin, dir);
  delay(10);
  for (long i = 0; i < steps; i++) {
    digitalWrite(stepperPin, HIGH);
    delayMicroseconds(300); 
    digitalWrite(stepperPin, LOW);
    delayMicroseconds(300); 
  }
}

void step(int index, long dist){
  move(dist > 0, dirs[index], steps[index], abs(dist));
  pos[index] += dist;
  pos[index] = pos[index] % stps ;

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
  pinMode(W_DIR, OUTPUT); pinMode(W_STP, OUTPUT);

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

    //moving magnets format: move dx dy dz
    //change this format when modyfying magnet numbers - currently expecting 3 motors
    //might add a configuration file such that it doesn't take modyfying both this and the python code later
    if(getValue(input, ' ', 0) == "mov" or getValue(input, ' ', 0) == "move"){
      for(int index = 0; index  < 4; index+=1){
        long val = parse_long(getValue(input,' ', index+1));
        step(index, val);
      } 
        }
    //position query
    //again, change the magic 3 here
    if(getValue(input, ' ', 0) == "pos"){
      String output = "";
      for(int i=0; i < 4; i++){
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
