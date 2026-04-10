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

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên ~50K chars đầu của sách chunk_size 500:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
|  AI Engineer| FixedSizeChunker (`fixed_size`) | 111 |500 | |
|  AI Engineer| SentenceChunker (`by_sentences`) |197 | 252.22| |
|  AI Engineer| RecursiveChunker (`recursive`) |132 |360.19 | |

### Strategy Của Tôi

**Loại:** [RecursiveChunker]

**Mô tả cách hoạt động:**
> RecursiveChunker chia văn bản theo thứ tự ưu tiên của các separator như `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng mới cắt theo ký tự nếu vẫn còn quá dài. Thuật toán sẽ cố giữ các đoạn lớn còn nguyên nghĩa trước, chỉ tách nhỏ hơn khi chunk vượt quá `chunk_size`. Cách này giúp chunk bám theo cấu trúc tự nhiên của tài liệu như paragraph, câu và section. Nhờ đó nội dung trong mỗi chunk thường mạch lạc hơn so với việc cắt cố định theo số ký tự.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Tài liệu nhóm chọn là sách *AI Engineering*, có cấu trúc rõ ràng theo chapter, section và paragraph nên recursive chunking tận dụng rất tốt các ranh giới tự nhiên đó. Strategy này giúp giữ được ngữ cảnh kỹ thuật tương đối đầy đủ trong mỗi chunk, từ đó hỗ trợ retrieval chính xác và dễ interpret hơn.

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| | best baseline | | | |
| | RecursiveChunker|132 |360.19 | |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi |Recursive |8/10 | - Giữ được ngữ cảnh theo paragraph/section nên top-k thường dễ đọc và sát ý hơn Hợp với tài liệu dạng sách kỹ thuật có nhiều heading và phân cấp nội dung rõ ràng. |  - Độ dài chunk không đồng đều, có thể làm score giữa các chunk hơi khó so sánh.Nếu metadata chương/mục chưa gán kỹ, retrieval vẫn có thể trả về chunk hơi rộng.|
| Công | Custom| 8/10| - Chunk có thể trace rõ về `page_id` và `chunk_id`, nên dễ kiểm tra retrieval trả về đoạn nào. Recursive chunking giữ ngữ cảnh tốt hơn fixed-size thông thường khi làm việc với tài liệu dài.| - Schema hiện tại chưa có field `part` hoặc `chapter`, nên filter theo chương chưa làm trực tiếp được. Nếu một ý nằm ở ranh giới giữa hai page hoặc hai chunk thì retrieval có thể bỏ sót một phần context.
|
| Thắng |Recursive|10/10|Bảo toàn tốt ngữ nghĩa của đoạn văn bản/header do respects markdown syntax boundaries. |Có thể sót những thông tin cần chuỗi ngữ cảnh quá lớn vượt quá `chunk_size`, bị cắt thành 2 chunks tách biệt làm giảm vector similarity. |
| Minh|Sentence  |8/10 |Mỗi chunk luôn kết thúc tại ranh giới câu → semantic coherence cao, embedding chất lượng tốt hơn.Không cần cấu hình `chunk_size` cứng → tự nhiên thích nghi với câu ngắn/dài trong sách. | Chunk dài khi gặp câu phức tạp (câu dài > 200 ký tự) → có thể vượt context window.Không tận dụng được cấu trúc đoạn/chương của sách (không biết đây là phần nào của Chapter 6 vs Chapter 1).|
| Hoàng |Retrieval  |8/10 |Phân bổ chunk khá đồng đều (Avg Length ~647.5 trên max 800) mà không làm gãy văn cảnh.Các khái niệm học thuật (như LLM-as-a-judge) được giữ trong trọn vẹn 1 đoạn mô tả lớn thay vì xé rách ra quá nhỏ. |Sinh ra vài chunk quá nhỏ (orphan chunks) nếu đoạn text vô cớ có nhiều dấu `\n` dư thừa. |
| Mong |Recursive|10/10 | Rất hiệu quả với văn bản có cấu trúc (Markdown/Book), giữ được ngữ cảnh toàn vẹn của đoạn văn.Tương thích tốt với Local Embedder khi xử lý ngôn ngữ tiếng Anh.|Phụ thuộc vào chất lượng của các separators; nếu text có nhiều noise (từ PDF parse) thì đôi khi vẫn bị chia cắt không mong muốn.|
| Huy |Custom — `HeadingChunker |10/10 | Metadata giàu (`section_title`, `heading_level`, `start_page`, `end_page`, `part="chapterN"`) → grounding rất rõ, dễ cite page trong agent answer.Query 4 (cross-chapter) lấy được **đúng cả 2 vế** trong top-2: Chapter 5 "Prompt Engineering" (0.660) + Chapter 7 "When to Finetune" (0.633) — minh họa HeadingChunker không bị bias về 1 chương duy nhất.|PDF-to-markdown parser đôi khi bắt nhầm paragraph fragment thành `####` heading → sinh vài chunk rác ở front matter (ví dụ một chunk có title *"Drawing on her deep expertise, AI Engineering is a comprehensive and) Query 5 (LLM-as-a-judge) có score top-1 chỉ 0.492 — thấp nhất trong 5 queries. Term "LLM-as-a-judge" được định nghĩa rải rác ở Chapter 3, không có section duy nhất bao trọn khái niệm → chunk đơn lẻ khó match strong.|

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:*
Theo tôi, strategy của Huy là phù hợp nhất cho domain này vì `HeadingChunker` tận dụng trực tiếp cấu trúc heading/chapter của sách *AI Engineering*. Cách chia này giữ được ngữ cảnh theo từng section lớn, đồng thời metadata như `section_title`, `start_page`, `end_page`, và `part="chapterN"` giúp retrieval rõ ràng, dễ filter và dễ giải thích nguồn khi trả lời. Đặc biệt với các câu hỏi học thuật hoặc cần đối chiếu nhiều chương, strategy này cho grounding tốt và dễ truy vết hơn so với các cách chunk thông thường.
---

## 4. My Approach — Cá nhân (10 điểm)

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

 "What is the difference between language models and large language models?",
    "What are the three layers of the AI engineering stack?",
    "How does RAG help ground LLM outputs in external knowledge?",
    "What are the main trade-offs between fine-tuning and prompt engineering?",
    "What is LLM-as-a-judge and when is it useful?",


### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
 | 1 | "What is the difference between language models and large language models?" | 0.4482 | "Both RAG and agents work with a lot of information..." |  |
  | 2 | "What are the three layers of the AI engineering stack?" | 0.3284 | "Our unique network of experts and innovators... |  |
  | 3 | "How does RAG help ground LLM outputs in external knowledge?" | 0.4521 | "RAG and Agents" | |
  | 4 | "What are the main trade-offs between fine-tuning and prompt engineering?" | 0.5027 | "<!-- page: 527 -->" |  |
  | 5 | "What is LLM-as-a-judge and when is it useful?" | 0.4 | "in your prompt. The model then works out what steps to take..." | |

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
