.PHONY: eval price price-update price-diff content xhs hotspot status help queue next schedule publish pstate pcheck ratio

# ── 配置 ──
BENCH ?= all
MODELS ?=
TOPIC ?=
TYPE ?= principle
XHS_MODE ?= local
DATE := $(shell date +%Y-%m-%d)

# ── Pipeline 入口 ──

help:
	@cat scripts/pipelines/README.md

status:
	@echo "📊 Pipeline 状态"
	@echo "─────────────────"
	@echo "评测数据: $$(ls content/eval-reports/ 2>/dev/null | wc -l | tr -d ' ') 份报告"
	@echo "价格数据: $$(python3 -c 'import json; d=json.load(open("scripts/pipelines/prices.json")); print(len(d["models"]), "个模型")' 2>/dev/null || echo 未初始化)"
	@echo "已创作:   $$(ls -d content/2* 2>/dev/null | wc -l | tr -d ' ') 期内容"
	@echo "─────────────────"
	@echo "make eval    — 跑模型评测"
	@echo "make price   — 查看API价格"
	@echo "make content — 生成内容"
	@echo "make xhs     — 出小红书图"
	@echo "make hotspot — 检查热点"
	@echo "make queue   — 查看发布队列"
	@echo "make next    — 下一个该发什么"
	@echo "make schedule TOPIC=x — 排入发布队列"
	@echo "make publish TOPIC=x PLATFORM=y — 标记已发布"
	@echo "make ratio   — 内容比例检查"

# ── 评测 Pipeline ──

eval:
	@mkdir -p content/eval-reports
	@echo "📊 跑模型评测..."
	@if [ "$(BENCH)" = "all" ]; then \
		python3 scripts/eval_benchmark.py --all --format md \
			$$(if [ -n "$(MODELS)" ]; then echo "--models $(MODELS)"; fi) \
			--output content/eval-reports/$(DATE)-all.md; \
	else \
		python3 scripts/eval_benchmark.py --bench $(BENCH) --format md \
			$$(if [ -n "$(MODELS)" ]; then echo "--models $(MODELS)"; fi) \
			--output content/eval-reports/$(DATE)-$(BENCH).md; \
	fi
	@echo "✅ 报告已保存到 content/eval-reports/"

# ── 价格 Pipeline ──

price:
	@python3 scripts/pipelines/price-pipeline.py show

price-update:
	@python3 scripts/pipelines/price-pipeline.py update

price-diff:
	@python3 scripts/pipelines/price-pipeline.py diff

# ── 内容 Pipeline ──

content:
	@if [ -z "$(TOPIC)" ]; then echo "❌ 请指定选题: make content TOPIC=<topic_name>"; exit 1; fi
	@python3 scripts/pipelines/content-pipeline.py create \
		--topic $(TOPIC) --type $(TYPE) --date $(DATE)

# ── 小红书 Pipeline ──

xhs:
	@if [ -z "$(TOPIC)" ]; then echo "❌ 请指定选题: make xhs TOPIC=<topic_name>"; exit 1; fi
	@python3 scripts/pipelines/xhs-pipeline.py generate \
		--topic $(TOPIC) --mode $(XHS_MODE) --date $(DATE)

# ── 热点 Pipeline ──

hotspot:
	@python3 scripts/pipelines/hotspot-pipeline.py check

# ── 发布调度 ──

queue:
	@python3 scripts/publish-scheduler.py queue

next:
	@python3 scripts/publish-scheduler.py next

schedule:
	@if [ -z "$(TOPIC)" ]; then echo "❌ 请指定选题: make schedule TOPIC=<topic_name>"; exit 1; fi
	@python3 scripts/publish-scheduler.py schedule $(TOPIC) --type $(TYPE)

publish:
	@if [ -z "$(TOPIC)" ] || [ -z "$(PLATFORM)" ]; then echo "❌ 用法: make publish TOPIC=<topic> PLATFORM=<weixin|xiaohongshu|bilibili|zhihu>"; exit 1; fi
	@python3 scripts/publish-scheduler.py publish $(TOPIC) $(PLATFORM)

pstate:
	@if [ -z "$(TOPIC)" ]; then echo "❌ 请指定选题: make pstate TOPIC=<topic_name>"; exit 1; fi
	@python3 scripts/publish-scheduler.py state $(TOPIC) $(if $(NEW_STATE),$(NEW_STATE),)

pcheck:
	@if [ -z "$(TOPIC)" ] || [ -z "$(PLATFORM)" ]; then echo "❌ 用法: make pcheck TOPIC=<topic> PLATFORM=<weixin|xiaohongshu|bilibili|zhihu>"; exit 1; fi
	@python3 scripts/publish-scheduler.py check $(TOPIC) $(PLATFORM)

ratio:
	@python3 scripts/publish-scheduler.py ratio
