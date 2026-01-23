package io.kamyarkian.ingestion;

import org.apache.kafka.clients.admin.NewTopic; // For Auto-Topic Creation
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringSerializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean; // Important for Topic Bean
import org.springframework.kafka.config.TopicBuilder;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.web.client.RestTemplate;

import java.util.Map;
import java.util.Properties;

@SpringBootApplication
@EnableScheduling
public class IngestionServiceApplication {

    private static final Logger logger = LoggerFactory.getLogger(IngestionServiceApplication.class);
    
    // [HOMEWORK REQ 1]: Target Topic Name
    private static final String TOPIC = "market-data-raw"; 
    private static final String BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT";

    private final KafkaProducer<String, String> producer;
    private final RestTemplate restTemplate;

    public static void main(String[] args) {
        SpringApplication.run(IngestionServiceApplication.class, args);
    }

    // [HOMEWORK REQ 1]: Auto-create topic if missing
    @Bean
    public NewTopic createRawTopic() {
        return TopicBuilder.name(TOPIC)
                .partitions(1)
                .replicas(1)
                .build();
    }

    public IngestionServiceApplication() {
        this.restTemplate = new RestTemplate();
        Properties props = new Properties();

        // Docker Connection
        String kafkaBroker = "kafka:29092"; 
        
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, kafkaBroker);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.ACKS_CONFIG, "1");

        this.producer = new KafkaProducer<>(props);
    }

    @Scheduled(fixedRate = 3000) // 3 Seconds Loop
    public void streamMarketData() {
        try {
            Map<String, String> response = restTemplate.getForObject(BINANCE_API_URL, Map.class);

            if (response != null && response.get("price") != null) {
                String priceStr = (String) response.get("price");
                double price = Double.parseDouble(priceStr);
                long timestamp = System.currentTimeMillis();

                String jsonPayload = String.format("{\"symbol\":\"BTC-USD\",\"price\":%.2f,\"timestamp\":%d}", price, timestamp);

                // [HOMEWORK REQ 2]: Send Message
                producer.send(new ProducerRecord<>(TOPIC, "btc-key", jsonPayload));
                
                // [HOMEWORK REQ 3]: Exact Success Metric Log
                logger.info("Message ingested successfully: {}", jsonPayload);
            }
        } catch (Exception e) {
            logger.error("Ingestion Failed: {}", e.getMessage());
        }
    }
}