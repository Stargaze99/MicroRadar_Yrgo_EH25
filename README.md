# MicroRadar Yrgo

Detta repo innehåller ett skolprojekt för kursen inbyggda system / IoT på Yrgo.

Projektet är en liten radar-liknande lösning byggd med Raspberry Pi Pico 2 W och MicroPython. En HY-SRF05 ultraljudssensor sitter på ett MG90S-servo som sveper mellan olika vinklar och mäter avstånd. Resultatet visas på en SPI OLED-skärm som en enkel radarvy, och värden skickas även via WiFi/MQTT.

Systemet har också en rotary encoder med tryckknapp som används för menyval på OLED-skärmen. Via menyn kan man se aktuell data och ändra vissa inställningar, till exempel servohastighet och hur ofta MQTT-meddelanden skickas.

Koden är uppdelad i moduler för sensor, servo, display, meny, encoder, MQTT och delat trådtillstånd.
