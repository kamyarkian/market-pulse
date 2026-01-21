package io.kamyarkian.ingestion;  // <--- Adjusted to match your folder

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import java.util.Map;

@Service
public class BinanceScheduler {

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final RestTemplate restTemplate;
    
    // API Link
    private final String BINANCE_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT";

    // Constructor Injection
    public BinanceScheduler(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
        this.restTemplate = new RestTemplate();
    }

    // Runs every 1000ms (1 second)
    @Scheduled(fixedRate = 1000)
    public void fetchRealPrice() {
        try {
            // 1. Fetch data from Binance
            Map response = restTemplate.getForObject(BINANCE_URL, Map.class);
            
            if (response != null && response.get("price") != null) {
                String price = (String) response.get("price");
                
                // 2. Create clean JSON payload
                String jsonPayload = String.format(
                    "{\"symbol\": \"BTC-USD\", \"price\": %s, \"source\": \"Binance-API\", \"timestamp\": %d}", 
                    price, System.currentTimeMillis()
                );

                // 3. Push to Kafka
                kafkaTemplate.send("market-data", jsonPayload);
                System.out.println("✅ [REAL-TIME] BTC Price: $" + price);
            }
        } catch (Exception e) {
            System.err.println("❌ Connection Error: " + e.getMessage());
        }
    }
}