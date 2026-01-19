package io.kamyarkian.ingestor;

import org.springframework.web.bind.annotation.*;
import org.springframework.kafka.core.KafkaTemplate;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/v1/data")
@RequiredArgsConstructor
public class MarketDataController {

    private final KafkaTemplate<String, String> kafkaTemplate;

    @PostMapping
    public String ingest(@RequestBody String payload) {
        // Send data to Kafka topic "market-data"
        kafkaTemplate.send("market-data", payload);
        return "Received & Sent to Kafka: " + payload;
    }
}