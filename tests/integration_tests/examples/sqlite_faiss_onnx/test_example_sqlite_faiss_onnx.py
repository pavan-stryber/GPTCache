import os
import time

from gptcache.adapter import openai
from gptcache import cache, Config
from gptcache.manager import get_data_manager, CacheBase, VectorBase
from gptcache.similarity_evaluation.distance import SearchDistanceEvaluation
from gptcache.embedding import Onnx


def test_sqlite_faiss_onnx():
    onnx = Onnx()

    sqlite_file = "sqlite.db"
    faiss_file = "faiss.index"
    if os.path.isfile(sqlite_file):
        os.remove(sqlite_file)
    if os.path.isfile(faiss_file):
        os.remove(faiss_file)
    cache_base = CacheBase("sqlite")
    vector_base = VectorBase("faiss", dimension=onnx.dimension)
    data_manager = get_data_manager(cache_base, vector_base, max_size=2000)

    def log_time_func(func_name, delta_time):
        print("func `{}` consume time: {:.2f}s".format(func_name, delta_time))

    cache.init(
        embedding_func=onnx.to_embeddings,
        data_manager=data_manager,
        similarity_evaluation=SearchDistanceEvaluation(),
        config=Config(log_time_func=log_time_func, similarity_threshold=0.9),
    )

    question = "what do you think about chatgpt"
    answer = "chatgpt is a good application"
    cache.import_data([question], [answer])

    mock_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "what do you think chatgpt"},
    ]

    start_time = time.time()
    from openai import OpenAI
    openai_client = OpenAI(
        api_key="API_KEY",
    )
    answer = openai.cache_openai_chat_complete(
        openai_client,
        model="gpt-3.5-turbo",
        messages=mock_messages,
    )
    end_time = time.time()
    print("cache hint time consuming: {:.2f}s".format(end_time - start_time))
    print(answer)

    is_exception = False
    try:
        openai.cache_openai_chat_complete(
            openai_client,
            model="gpt-3.5-turbo",
            messages=mock_messages,
            cache_factor=100,
        )
    except Exception:
        is_exception = True

    assert is_exception

    mock_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "what do you feel like chatgpt"},
    ]
    is_exception = False
    try:
        openai.cache_openai_chat_complete(
            openai_client,
            model="gpt-3.5-turbo",
            messages=mock_messages,
        )
    except Exception:
        is_exception = True

    assert is_exception

    is_exception = False
    try:
        openai.cache_openai_chat_complete(
            openai_client,
            model="gpt-3.5-turbo",
            messages=mock_messages,
            cache_factor=0.5,
        )
    except Exception:
        is_exception = True

    assert not is_exception
