from config import Config
from services.medquad_preprocessor import iter_medquad_documents


def test_existing_medquad_has_usable_question_answer_pairs():
    record_count = 0
    first_document = None
    for document in iter_medquad_documents(Config.MEDQUAD_CSV_PATH):
        first_document = first_document or document
        assert document.question and document.answer
        record_count += 1
    assert record_count == 16407
    assert first_document is not None and first_document.source_row_id == 0
