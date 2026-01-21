package io.kamyarkian.ingestion;  // <--- Fixed: Matches your folder name

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class IngestionServiceApplication {  // <--- Fixed: Matches your file name

    public static void main(String[] args) {
        SpringApplication.run(IngestionServiceApplication.class, args);
    }
}