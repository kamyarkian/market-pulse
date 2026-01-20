package io.kamyarkian.ingestion;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import java.util.Random;

@Service
public class MarketProducer {

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final Random random = new Random();

    // Constructor Injection
    public MarketProducer(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    // Runs every 1000ms (1 second)
    @Scheduled(fixedRate = 1000)
    public void generateMarketData() {
        double price = 95000 + (random.nextDouble() * 2000); // Price fluctuation
        int volume = random.nextInt(100); // Random trade volume
        long timestamp = System.currentTimeMillis();

        // Creating JSON manually (Professional & Efficient)
        String jsonMessage = String.format(
            "{\"symbol\": \"BTC-USD\", \"price\": %.2f, \"volume\": %d, \"timestamp\": %d}",
            price, volume, timestamp
        );

        System.out.println("📤 Sending JSON: " + jsonMessage);
        
        // Send to Kafka
        kafkaTemplate.send("market-data", jsonMessage);
    }
}