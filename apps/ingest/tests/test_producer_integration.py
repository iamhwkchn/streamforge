"""
Integration tests for producer.py — requires Redpanda running on localhost:9092.

Run after: docker compose up redpanda redpanda-console

Uses a dedicated test topic (retail.events.test) that is created before the
test run and deleted automatically after — retail.events is never touched.
"""
import json
import re
import sys
from pathlib import Path

import pytest
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import NoBrokersAvailable, UnknownTopicOrPartitionError

sys.path.insert(0, str(Path(__file__).parent.parent))
import producer as prod

BROKER = "localhost:9092"
TEST_TOPIC = "retail.events.test"
BATCH_SIZE = 10
XLSX_PATH = str(
    Path(__file__).parent.parent.parent.parent / "data" / "raw_datasets" / "online_retail_II.xlsx"
)


# ---------------------------------------------------------------------------
# Skip all tests if Redpanda isn't reachable
# ---------------------------------------------------------------------------

def redpanda_is_available() -> bool:
    try:
        p = KafkaProducer(bootstrap_servers=BROKER)
        p.close()
        return True
    except NoBrokersAvailable:
        return False


skip_if_no_broker = pytest.mark.skipif(
    not redpanda_is_available(),
    reason="Redpanda not reachable on localhost:9092 — start with: docker compose up redpanda",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def test_topic():
    """Creates retail.events.test before the module runs, deletes it after."""
    admin = KafkaAdminClient(bootstrap_servers=BROKER)
    admin.create_topics([NewTopic(name=TEST_TOPIC, num_partitions=1, replication_factor=1)])
    yield TEST_TOPIC
    try:
        admin.delete_topics([TEST_TOPIC])
    except UnknownTopicOrPartitionError:
        pass
    admin.close()


@pytest.fixture(scope="module")
def rows():
    return prod.load_dataset(XLSX_PATH)[:BATCH_SIZE]


@pytest.fixture(scope="module")
def real_producer():
    p = KafkaProducer(
        bootstrap_servers=BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    yield p
    p.close()


def make_consumer(topic: str) -> tuple[KafkaConsumer, TopicPartition]:
    """Returns a consumer + TopicPartition already assigned and seeked to end."""
    tp = TopicPartition(topic, 0)
    consumer = KafkaConsumer(
        bootstrap_servers=BROKER,
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        consumer_timeout_ms=5000,
    )
    consumer.assign([tp])
    consumer.seek_to_end(tp)
    return consumer, tp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_if_no_broker
class TestProducerIntegration:

    def test_can_connect_to_broker(self):
        p = KafkaProducer(bootstrap_servers=BROKER)
        assert p.bootstrap_connected()
        p.close()

    def test_publishes_batch_without_error(self, test_topic, real_producer, rows):
        for row in rows:
            real_producer.send(test_topic, value=row)
        real_producer.flush()
        # flush() is synchronous — if it returns, all messages were acknowledged

    def test_messages_arrive_in_topic(self, test_topic, real_producer, rows):
        tp = TopicPartition(test_topic, 0)
        consumer = KafkaConsumer(bootstrap_servers=BROKER, enable_auto_commit=False)
        consumer.assign([tp])

        before = consumer.end_offsets([tp])[tp]

        for row in rows:
            real_producer.send(test_topic, value=row)
        real_producer.flush()

        after = consumer.end_offsets([tp])[tp]
        consumer.close()

        assert after - before == BATCH_SIZE

    def test_received_messages_have_correct_fields(self, test_topic, real_producer, rows):
        consumer, _ = make_consumer(test_topic)

        for row in rows:
            real_producer.send(test_topic, value=row)
        real_producer.flush()

        received = []
        for msg in consumer:
            received.append(msg.value)
            if len(received) >= BATCH_SIZE:
                break
        consumer.close()

        required = {"invoice", "stock_code", "description", "quantity",
                    "invoice_date", "price", "country"}
        for msg in received:
            assert required.issubset(msg.keys())

    def test_invoice_date_in_message_is_iso_string(self, test_topic, real_producer, rows):
        consumer, _ = make_consumer(test_topic)

        for row in rows:
            real_producer.send(test_topic, value=row)
        real_producer.flush()

        received = []
        for msg in consumer:
            received.append(msg.value)
            if len(received) >= BATCH_SIZE:
                break
        consumer.close()

        for msg in received:
            assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", msg["invoice_date"])
