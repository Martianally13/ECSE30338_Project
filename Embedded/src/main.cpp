#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "env.h"


#define FanPin 21
#define LightPin 22
#define LDRPin 9
#define oneWireBus 4 
OneWire oneWire(oneWireBus);
DallasTemperature sensors(&oneWire);

int detected;


void setup() 
{
  pinMode(FanPin, OUTPUT);
  pinMode(LightPin, OUTPIN);
  pinMode(LDRPin, INPUT);
  pinMode(oneWireBus, INPUT);

  sensors.begin();

  Serial.begin(9600);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  Serial.println("Connecting");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to WiFi network with IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop()
 {
    //Temperature Data
    sensors.requestTemperatures();
    Serial.print("Temperature is: ");
    float temperature = sensors.getTempCByIndex(0);
    Serial.print(temperature);
    Serial.print((char)176);
    Serial.print("C");

    Serial.print("\n");
    //Presence Data
    detect = digitalRead(LDRPin);
    Serial.print("LDR Data shows binary: ");
    Serial.print(detect);
    Serial.print("\n----------------\n");

//--------------------------------------------------------------------------------------------

  if(WiFi.status()== WL_CONNECTED)
  {
    
    HTTPClient http;  
    String httpResponse;
    http.begin(POST_ENDPOINT);
    http.addheader("Content-Type","application/json");
   
    StaticJsonDocument<1024> doc1;
    doc1["Temperature"] = temperature;
    doc1["Presence"] = !detect;

    serializeJson(doc1,http_request_data);
    String http_request_data;

    int httpPOSTCode = http.POST(http_request_data);

    if (httpPOSTCode > 0)
      {
        Serial.print("HTTP Response code: ");
        Serial.println(httpPOSTCode);

        //Serial.print("Response from server: ");
        //http_response = http.getString();
        //Serial.println(http_response1);
      }
      else
      {   
        Serial.print("Error code: ");
        Serial.println(httpPOSTCode);
      } 

      http.end();
//--------------------------------------------------------------------------------------------
      http.begin(GET_ENDPOINT)

      int httpGETCode = http.GET();

          if (httpGETCode > 0) 
          {
            Serial.print("HTTP Response code: ");
            Serial.println(httpGETCode); 

            Serial.print("HTTP Response from server: ");
            httpResponse = http.getString();
            Serial.println(httpResponse);
          else 
          {
          Serial.print("Error Code: ");
          Serial.println(httpGETCode);
          }
          http.end();
//--------------------------------------------------------------------------------------------

            StaticJsonDocument<1024> doc2;
            DeserializationError error = deserializeJson(doc2, httpResponse);

            if (error) 
            {
              Serial.println("deserializeJson() failed: ");
              Serial.println(error.c_str());
              return;
            }

            bool lightState = doc2["light"];
            bool fanState = doc2["fan"];

            Serial.println("light: ");
            Serial.print(lightState);

            Serial.println("Fan: ");
            Serial.print(fanState);

            digitalWrite(FanPin, fanState);
            digitalWrite(LightPin, lightState);


        }                   
  }
  else 
  {   
    Serial.println("Not Successfull");
    return;
  }
}