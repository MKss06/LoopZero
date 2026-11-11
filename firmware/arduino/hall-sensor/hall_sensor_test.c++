const int hallPin = A0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int leitura = analogRead(hallPin);

  float tensao = leitura * (5.0 / 1023.0);

  Serial.print("ADC: ");
  Serial.print(leitura);

  Serial.print(" | Tensao: ");
  Serial.println(tensao, 3);

  delay(200);
}