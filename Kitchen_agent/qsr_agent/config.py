# # Copyright 2025 Google LLC
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

# import os
# from dataclasses import dataclass

# import google.auth

# # To use AI Studio credentials:
# # 1. Create a .env file in the /app directory with:
# #    GOOGLE_GENAI_USE_VERTEXAI=FALSE
# #    GOOGLE_API_KEY=PASTE_YOUR_ACTUAL_API_KEY_HERE
# # 2. This will override the default Vertex AI configuration
# _, project_id = google.auth.default()
# os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
# os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
# os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")


# @dataclass
# class ResearchConfiguration:
#     """Configuration for research-related models and parameters.

#     Attributes:
#         critic_model (str): Model for evaluation tasks.
#         worker_model (str): Model for working/generation tasks.
#         max_search_iterations (int): Maximum search iterations allowed.
#     """

#     critic_model: str = "gemini-2.5-pro"
#     worker_model: str = "gemini-2.5-flash"
#     max_search_iterations: int = 5


# config = ResearchConfiguration()




# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from dataclasses import dataclass
from dotenv import load_dotenv

import google.auth

load_dotenv()



# Read environment variable to determine if Vertex AI should be used
USE_VERTEX = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() == "true"

if USE_VERTEX:
    # ---------------------------
    # Vertex AI Mode (requires ADC)
    # ---------------------------
    try:
        credentials, project_id = google.auth.default()
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
        os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
    except Exception as e:
        raise RuntimeError(
            "Vertex AI mode is enabled, but Google Cloud ADC credentials "
            "were not found. Set GOOGLE_GENAI_USE_VERTEXAI=FALSE to use API Key mode.\n"
            f"Original error: {e}"
        )
else:
    # ---------------------------
    # API KEY MODE (NO CREDENTIALS NEEDED)
    # ---------------------------
    # Dummy project id — not used, but required by ADK runtime
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "api-key-mode")
    os.environ["GOOGLE_CLOUD_LOCATION"] = "global"


@dataclass
class ResearchConfiguration:
    """
    Configuration for research models and parameters.
    """
    critic_model: str = "gemini-2.0-flash"
    worker_model: str = "gemini-2.5-flash"
    vision_model: str = "gemini-2.0-flash"   # ✅ ADD THIS

    max_search_iterations: int = 5


# Export config object
config = ResearchConfiguration()
