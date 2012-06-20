"""
Redis check tests.
"""

import logging
import unittest

import nose.tools as t

from checks.db.redisDb import Redis as RedisCheck
import redis


logger = logging.getLogger()

class TestRedis(object):

    def test_redis_default(self):
        db = redis.Redis(db=14) # Datadog's test db
        db.flushdb()
        db.set("key1", "value")
        db.set("key2", "value")
        db.setex("expirekey", "expirevalue", 1000)
        
        r = RedisCheck(logger)
        metrics = self._sort_metrics(r.check({}))
        assert metrics, "we returned metrics"

        print metrics

        # Assert we have values, timestamps and tags for each metric.
        for m in metrics:
            assert isinstance(m[1], int)    # timestamp
            assert isinstance(m[2], float)  # value
            tags = m[3]["tags"]
            expected_tags = ["redis_host:localhost", "redis_port:6379"]
            for e in expected_tags:
                assert e in tags

        # Assert we have the rest of the keys.
        remaining_keys = [m[0] for m in metrics]
        expected = ['redis.mem.used', 'redis.net.clients', 'redis.net.slaves']
        for e in expected:
            assert e in remaining_keys, e

        # Assert that the keys metrics are tagged by db. just check db0, since
        # it's the only one we can guarantee is there.
        db_metrics = self._sort_metrics([m for m in metrics if m[0] in ['redis.keys',
        'redis.expires'] and "redis_db:db14" in m[3]["tags"]])
        t.assert_equals(2, len(db_metrics))

        t.assert_equal('redis.expires', db_metrics[0][0])
        t.assert_equal(1, db_metrics[0][2]) 

        t.assert_equal('redis.keys', db_metrics[1][0])
        t.assert_equal(3, db_metrics[1][2]) 

        # Run one more check and ensure we get total command count
        metrics = self._sort_metrics(r.check({}))
        keys = [m[0] for m in metrics]
        assert 'redis.net.commands' in keys

    def _sort_metrics(self, metrics):
        def sort_by(m):
            return m[0], m[1], m[3]
        return sorted(metrics, key=sort_by)
