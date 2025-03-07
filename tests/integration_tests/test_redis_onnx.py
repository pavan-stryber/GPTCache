import random
from unittest.mock import patch

from gptcache import Cache
from gptcache.adapter import openai
from gptcache.adapter.api import init_similar_cache
from gptcache.embedding import Onnx
from gptcache.manager import manager_factory
from gptcache.processor.pre import last_content
from gptcache.utils.response import get_message_from_openai_answer


def test_redis_sqlite():
    encoder = Onnx()

    redis_data_managers = [
        manager_factory(
            "sqlite,redis",
            data_dir=str(random.random()),
            vector_params={"dimension": encoder.dimension},
        ),
        manager_factory(
            "redis,redis",
            data_dir=str(random.random()),
            scalar_params={"global_key_prefix": "gptcache_scalar"},
            vector_params={"dimension": encoder.dimension, "namespace": "gptcache_vector", "collection_name": "cache_vector"},
        )
    ]
    for redis_data_manager in redis_data_managers:
        redis_cache = Cache()
        init_similar_cache(
            cache_obj=redis_cache,
            pre_func=last_content,
            embedding=encoder,
            data_manager=redis_data_manager,
        )
        question = "what's github"
        expect_answer = "GitHub is an online platform used primarily for version control and coding collaborations."

        redis_cache.data_manager.save(question, expect_answer, redis_cache.embedding_func(question))

        from openai import OpenAI
        response = openai.cache_openai_chat_complete(
            OpenAI(
                api_key="API_KEY",
            ),
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "can you explain what GitHub is"},
            ],
            cache_obj=redis_cache,
        )
        answer_text = get_message_from_openai_answer(response)
        assert answer_text == expect_answer, answer_text