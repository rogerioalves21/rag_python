from app.config import (
    get_text_splitter,
    
)
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
import os
import time
from rich import print
import asyncio
from app.api.extractors.pdf_extractor import PdfExtractor
from app.api.services.metadata_service import MetadataService
import onnxruntime as rt

sess_options = rt.SessionOptions()
sess_options.enable_profiling = True
sess_options.log_severity_level = 0 # Verbose
sess_options.execution_mode = rt.ExecutionMode.ORT_PARALLEL
sess_options.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
sess_options.inter_op_num_threads = 4
sess_options.intra_op_num_threads = 4
sess_options.add_session_config_entry("session.intra_op.allow_spinning", "0")

async def task(__folder: str, __arquivo: str):
    __doc_path_pdf = __folder + __arquivo
    __loader       = PdfExtractor(__doc_path_pdf, __arquivo, MetadataService())
    await __loader.extract()

async def main():
    t0 = time.time()
    count = 0
    __documents = []
    __folder = './files/pdfs/'
    __arquivos = os.listdir(__folder)
    for __arquivo in __arquivos:
        __doc_path_pdf = __folder + __arquivo
        __loader       = PdfExtractor(__doc_path_pdf, __arquivo, MetadataService())
        __document = await __loader.extract()
        __documents.extend(__document)
    print(__documents)
    print(f'all done, {count} documents in {int(int(time.time() - t0)/60)} minutos')

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    