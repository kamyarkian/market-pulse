package io.kamyarkian.ingestion;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling; // <--- ADDED THIS IMPORT

@SpringBootApplication
@EnableScheduling  // <--- ADDED THIS: Enables the internal timer
public class IngestionServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(IngestionServiceApplication.class, args);
    }

}