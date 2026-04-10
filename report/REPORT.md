# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** [Trần Minh Toàn]
**Nhóm:** [E4]
**Ngày:** [10/04]

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
- High cosine similarity nghĩa là độ tương đồng cao giữa hai vector, với giá trị gần 1 cho thấy chúng gần như cùng hướng trong không gian vector. Điều này thường được dùng để đo mức độ giống nhau giữa câu từ, hình ảnh, âm thanh, ...

**Ví dụ HIGH similarity:**
- Sentence A: "Chào bạn"
- Sentence B: "Rất vui được gặp bạn"
- Tại sao tương đồng: Cả hai câu đều nằm trong ngữ cảnh chào hỏi.

**Ví dụ LOW similarity:**
- Sentence A: "Cơm hôm nay ngon thật"
- Sentence B: "Giá vàng hôm nay tăng mạnh"
- Tại sao khác: Hai câu hoàn toàn khác chủ đề ngữ cảnh, không có từ vựng chung, không có context liên quan, và thuộc hai lĩnh vực hoàn toàn khác nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
- Cosine similarity đo **góc giữa các vector** (hướng/orientation) thay vì khoảng cách tuyệt đối, nên không bị ảnh hưởng bởi độ dài văn bản - hai câu có nội dung giống nhau sẽ có cosine similarity cao dù một câu dài hơn. Euclidean distance đo khoảng cách trong không gian, bị ảnh hưởng bởi magnitude của vector, dẫn đến văn bản dài hơn có thể bị coi là "khác biệt" hơn dù nghĩa tương tự.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

- num_chunks = ceil((doc_length - overlap) / (chunk_size - overlap))
- num_chunks = ceil((10,0000 - 50) / (500 - 50)) = 222.2

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

**Chunk count sẽ TĂNG lên** khi overlap tăng. Ví dụ: với chunk size 200 và overlap 100, mỗi chunk chỉ "tiến" được 100 token mới (200-100), nên cần nhiều chunk hơn để cover toàn bộ văn bản so với overlap nhỏ hơn.

**Tại sao muốn overlap nhiều hơn:**
- **Giữ ngữ cảnh liên tục**: Thông tin quan trọng ở cuối chunk này vẫn xuất hiện ở đầu chunk kế tiếp
- **Tránh mất thông tin**: Câu hoặc đoạn văn quan trọng không bị cắt đứt giữa 2 chunk
- **Cải thiện retrieval**: Khi tìm kiếm, có nhiều cơ hội hơn để tìm thấy thông tin liên quan vì nó xuất hiện trong nhiều chunk
- **Trade-off**: Overlap cao = nhiều chunk hơn = tốn storage và xử lý nhiều hơn, nhưng quality tốt hơn
---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** [Sách AI Engineer]

**Tại sao nhóm chọn domain này?**

Quyển sách thuộc lĩnh vực AI phù hợp với chuyên ngành mà nhóm đang theo chọn.


### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | AI Engineer| Chip Huyen | ~1M  | `book`, `part`, `chapter`, `section`, `author`, `source`|


### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `book` | string | `AI Engineering` | Giúp giới hạn kết quả đúng cuốn sách, giảm nhiễu từ tài liệu khác. |
| `part` | string | `Foundation Models` | Hữu ích khi gom các nội dung cùng nhóm chủ đề lớn để filter nhanh hơn. |
| `chapter` | string | `Chapter 1. Introduction to Building AI Applications with Foundation Models` | Cho phép truy hồi chính xác theo chương khi câu hỏi nhắm vào một phần cụ thể. |
| `section` | string | `The Rise of AI Engineering` | Giúp lấy đúng tiểu mục liên quan nhất, giữ ngữ cảnh hẹp và sát câu hỏi hơn. |
---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### 3.1. Baseline analysis

Tôi benchmark trên khoảng `50K` ký tự đầu của tài liệu bằng lệnh `python -m src.benchmark`. Kết quả gần nhất ghi nhận như sau:

| Strategy | Cấu hình | Chunk Count | Avg Length | Nhận xét nhanh |
|---|---|---:|---:|---|
| `FixedSizeChunker` | `chunk_size=350, overlap=80` | 185 | 349.8 | Ổn định, dễ kiểm soát kích thước nhưng không hiểu cấu trúc sách |
| `SentenceChunker` | `max_sentences_per_chunk=2` | 492 | 100.4 | Rất coherent theo câu nhưng dễ mất ngữ cảnh dài |
| `RecursiveChunker` | `chunk_size=300` | 230 | 206.0 | Cân bằng giữa độ dài và sự tự nhiên của chunk |
| `BookAwareChunker` | `target_chunk_size=100` | 475 | 160.1 | Giữ heading context tốt, dễ trace về section |

### 3.2. Strategy của tôi

**Strategy được chọn:** `BookAwareChunker`

**Ý tưởng chính:**
- Bỏ phần noise từ Markdown export như YAML front matter, `<!-- page: ... -->`, và Table of Contents.
- Tận dụng heading (`#`, `##`, `###`, `####`) để giữ ngữ cảnh theo section.
- Gắn prefix kiểu `Section: Chapter > Section > Subsection` vào từng chunk để tăng traceability.
- Nếu block quá dài, fallback về `RecursiveChunker` để chia nhỏ tự nhiên hơn.

**Vì sao strategy này phù hợp với `ai_engineer.md`?**  
Tài liệu của nhóm là một cuốn sách dài, có cấu trúc chương/mục rất rõ. Nếu chỉ cắt theo số ký tự thì dễ mất ranh giới ngữ nghĩa. `BookAwareChunker` phù hợp hơn vì nó tận dụng chính cấu trúc học thuật của sách, đồng thời loại bỏ nhiều phần nhiễu do PDF-to-Markdown conversion tạo ra.

### 3.3. Code snippet (rút gọn)

```python
class BookAwareChunker:
    def chunk(self, text: str) -> list[str]:
        cleaned = self._strip_front_matter(text.replace("\r\n", "\n"))
        lines = cleaned.splitlines()
        ...
        # bỏ page markers / TOC noise
        # gom paragraph theo heading context
        # fallback sang RecursiveChunker nếu block quá dài
        return self._merge_small_chunks(chunks)
```

### 3.4. So sánh strategy của tôi với baseline

| Strategy | Điểm mạnh | Điểm yếu |
|---|---|---|
| `FixedSizeChunker` | Dễ cài đặt, dễ dự đoán kích thước | Cắt “mù”, dễ vỡ ngữ nghĩa |
| `SentenceChunker` | Coherence tốt ở mức câu | Không tận dụng được cấu trúc chapter/section |
| `RecursiveChunker` | Giữ paragraph và câu khá tự nhiên | Chưa xử lý noise đặc thù của file sách |
| `BookAwareChunker` | Giữ context theo heading, trace nguồn tốt hơn | Nhiều chunks hơn, cần tuning `target_chunk_size` |

### 3.5. So sánh với thành viên khác trong nhóm

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm cần cải thiện |
|---|---|---:|---|---|
| Tôi | `BookAwareChunker` | 8/10 | Khai thác heading và structure của sách tốt | Cần tuning thêm metadata/filtering |
| Công | Custom | 8/10 | Có `page_id`, `chunk_id`, dễ trace nguồn | Chưa có `part`/`chapter` để filter trực tiếp |
| Thắng | Recursive | 10/10 | Tôn trọng markdown boundaries khá tốt | Có thể mất ngữ cảnh khi ý quá dài |
| Minh | Sentence | 8/10 | Chunk coherent, dễ embed | Không biết chunk thuộc chapter nào |
| Hoàng | Retrieval-focused | 8/10 | Chunk phân bố đều, ít gãy văn cảnh | Có thể sinh orphan chunks |
| Mong | Recursive | 10/10 | Hợp với văn bản kỹ thuật tiếng Anh | Vẫn phụ thuộc mạnh vào separator quality |
| Huy | `HeadingChunker` | 10/10 | Metadata giàu, grounding rất rõ | Parser có thể sinh vài heading rác |

**Theo tôi, strategy tốt nhất cho domain này là gì?**  
Trong nhóm, `HeadingChunker` của Huy là strategy mạnh nhất vì tận dụng trực tiếp chapter/section metadata của sách để grounding. Tuy nhiên, với implementation cá nhân của tôi, `BookAwareChunker` là bước cải tiến hợp lý và sát với dữ liệu nhất, vì nó giải quyết đúng vấn đề noise và structure của `ai_engineer.md`.

---

## 4. My Approach — Phần Cá Nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Tôi dùng regex để tách câu theo các dấu kết thúc phổ biến như `.`, `!`, `?` kết hợp với khoảng trắng hoặc xuống dòng phía sau. Sau khi split, tôi loại bỏ khoảng trắng thừa và gom nhiều câu lại thành từng chunk dựa trên `max_sentences_per_chunk`. Cách này giúp các chunk ngắn gọn, dễ đọc và vẫn giữ được ý tương đối trọn vẹn.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Tôi cài đặt recursive chunking bằng cách thử tách văn bản theo thứ tự ưu tiên của các separator: `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là cắt theo ký tự nếu vẫn quá dài. Base case là khi đoạn hiện tại rỗng, nhỏ hơn `chunk_size`, hoặc không còn separator nào để dùng. Cách này giúp thuật toán ưu tiên giữ nguyên paragraph và câu trước khi phải tách nhỏ hơn, nên chunk thường tự nhiên và mạch lạc hơn.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Tôi lưu mỗi document dưới dạng một record gồm `id`, `content`, `metadata` và `embedding`, trong đó embedding được tạo từ `embedding_fn` (mặc định là mock embedder). Khi search, tôi embed câu query rồi tính độ tương đồng bằng dot product giữa vector query và các vector đã lưu, sau đó sắp xếp giảm dần theo score và lấy top-k kết quả phù hợp nhất.

**`search_with_filter` + `delete_document`** — approach:
>  Với `search_with_filter`, tôi filter các record theo `metadata_filter` trước, rồi mới chạy similarity search trên tập đã lọc để tăng precision. Với `delete_document`, tôi xóa tất cả record có `id` hoặc `metadata['doc_id']` trùng với document cần xóa, rồi trả về `True/False` tùy theo có xóa được dữ liệu hay không.

### KnowledgeBaseAgent

**`answer`** — approach:
>  Tôi áp dụng mô hình RAG đơn giản: đầu tiên retrieve các chunk liên quan nhất từ `EmbeddingStore`, sau đó ghép chúng thành phần context trong prompt. Prompt được tổ chức theo dạng “Context → Question → Answer” để LLM hoặc hàm demo có thể sinh câu trả lời dựa trên nội dung đã truy hồi. Cách này giúp câu trả lời bám sát dữ liệu trong knowledge base thay vì trả lời hoàn toàn theo trí nhớ mô hình.

### Test Results

```
# Paste output of: pytest tests/ -v
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Python is used for machine learning. | Python is popular in AI applications. | high | 0.82 | Đúng |
| 2 | Vector stores support similarity search. | Embeddings help retrieve relevant chunks. | high | 0.76 | Đúng |
| 3 | Fine-tuning customizes a model with new data. | Prompt engineering changes the instructions given to a model. | high | 0.61 | Đúng |
| 4 | The weather is sunny today. | Neural networks are used in deep learning. | low | 0.09 | Đúng |
| 5 | Cats are common household pets. | Large language models are trained on massive text corpora. | low | 0.04 | Đúng |


**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả ở cặp 3 là đáng chú ý nhất vì dù fine-tuning và prompt engineering là hai kỹ thuật khác nhau, embedding vẫn cho điểm tương đồng khá cao do chúng cùng thuộc ngữ cảnh tối ưu hóa mô hình và đều liên quan đến việc điều khiển hành vi của LLM. Điều này cho thấy embeddings không chỉ dựa vào từ khóa bề mặt mà còn nắm được mức độ liên quan về mặt ngữ nghĩa và chủ đề.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
 | 1 | "What is the difference between language models and large language models?" |
  | 2 | "What are the three layers of the AI engineering stack?" | 
  | 3 | "How does RAG help ground LLM outputs in external knowledge?"| 
  | 4 | "What are the main trade-offs between fine-tuning and prompt engineering?" | 
  | 5 | "What is LLM-as-a-judge and when is it useful?" | 


### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
 | 1 | "What is the difference between language models and large language models?" | 0.5323 | "These frameworks can even suggest common finetuning methods with sensible default hyperparameters...." |  |
  | 2 | "What are the three layers of the AI engineering stack?" | 0.4207 | "As AI's capabilities expand daily, predicting its future possibilities becomes increasingly..." |  |
  | 3 | "How does RAG help ground LLM outputs in external knowledge?" | 0.4228 | "Combine the original query and the retrieved data to create a prompt in the format expected by the.." | |
  | 4 | "What are the main trade-offs between fine-tuning and prompt engineering?" |0.4483 | "Given the context of "My favorite color is ..." as shown in Figure 2-14, if "red" has a 30% chance..." |  |
  | 5 | "What is LLM-as-a-judge and when is it useful?" |0.4572 | "If this small dataset is sufficient to achieve your desirable performance, that's great..." | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Điều hay nhất tôi học được từ các thành viên khác là việc tận dụng metadata và cấu trúc heading của tài liệu có thể cải thiện retrieval rất rõ. Đặc biệt, strategy của Huy cho thấy khi chunk bám theo chapter/section và có metadata như `section_title`, `page`, `part`, thì kết quả không chỉ chính xác hơn mà còn dễ giải thích nguồn hơn.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Qua demo của nhóm khác, tôi nhận ra rằng không phải cứ chunk nhỏ là sẽ tốt hơn cho retrieval. Nhiều trường hợp chunk quá ngắn làm mất ngữ cảnh, trong khi chunk vừa phải và bám theo cấu trúc tự nhiên của tài liệu lại cho kết quả ổn định và hữu ích hơn.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> Nếu làm lại, tôi sẽ đầu tư nhiều hơn vào bước chuẩn hóa dữ liệu đầu vào và gán metadata chi tiết ngay từ đầu, ví dụ thêm page number, section title và chapter label cho từng chunk. Tôi cũng sẽ thử thêm một strategy kiểu heading-based để so sánh trực tiếp với recursive chunking và tối ưu retrieval tốt hơn cho tài liệu dạng sách.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 10 / 10 |
| Chunking strategy | Nhóm | 14 / 15 |
| My approach | Cá nhân | 9 / 10 |
| Similarity predictions | Cá nhân | 5 / 5 |
| Results | Cá nhân | 9 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 5 / 5 |
| **Tổng** | | **87 / 100** |
