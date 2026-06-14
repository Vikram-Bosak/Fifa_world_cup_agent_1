import sys
import os
import json
sys.path.append(os.path.abspath("."))
from common.seo_generator import analyze_video_for_editing

task = {
    "title": "When Zlatan made his #FIFAWorldCup debut 🇸🇪🤩",
    "source": "FIFA World Cup"
}
result = analyze_video_for_editing(task)
print(json.dumps(result, indent=4))
