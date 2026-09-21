# ru-masha-200

English below.

Женский русский голос для RVC v2. В архиве `ru-masha-200.zip` из [релиза](https://github.com/Friskes/voice-changer/releases): `ru-masha_200e_30600s.pth` (53 МБ) и `ru-masha.index` (420 МБ).

| Параметр | Значение |
| --- | --- |
| Данные | 45 минут актрисы Маши (`speaker_id` M) из корпуса [Dialogs](https://huggingface.co/datasets/langswap/dialogs-ru-emotional-conversations): 55% happy, 35% neutral, 10% surprise |
| Претрейн | [SnowieV3.1 40k](https://huggingface.co/MUSTAR/SnowieV3.1-40k), лицензия автором не указана |
| Обучение | Applio 3.6.5, 200 эпох, 30 600 шагов, batch 8, 40 кГц, HiFi-GAN, contentvec, rmvpe |
| Воспроизвести | `train-voice.bat M ru-masha 200` |

Модель — производная работа от Dialogs, поэтому на неё действует [лицензия OpenRAIL](LICENSE-Dialogs-OpenRAIL.md) этого корпуса. Скачивая и используя модель, ты соглашаешься соблюдать ограничения из её раздела 2; при передаче модели дальше приложи копию лицензии. Актёры корпуса дали письменное согласие на открытую публикацию и законное использование записей.

Авторы корпуса просят ссылаться на статью: I. Shigabeev, I. Latyshev. *Dialogs: A Studio-Quality Expressive Conversational Russian Speech Corpus for Dialog Assistants*. Interspeech 2026. <https://arxiv.org/abs/2607.14310>

## English

A female Russian voice for RVC v2. `ru-masha-200.zip` from the [release](https://github.com/Friskes/voice-changer/releases) holds `ru-masha_200e_30600s.pth` (53 MB) and `ru-masha.index` (420 MB).

| Parameter | Value |
| --- | --- |
| Data | 45 minutes of the actress Masha (`speaker_id` M) from the [Dialogs](https://huggingface.co/datasets/langswap/dialogs-ru-emotional-conversations) corpus: 55% happy, 35% neutral, 10% surprise |
| Pretrain | [SnowieV3.1 40k](https://huggingface.co/MUSTAR/SnowieV3.1-40k); its author states no license |
| Training | Applio 3.6.5, 200 epochs, 30,600 steps, batch 8, 40 kHz, HiFi-GAN, contentvec, rmvpe |
| Reproduce | `train-voice.bat M ru-masha 200` |

The model is a derivative of Dialogs, so that corpus's [OpenRAIL license](LICENSE-Dialogs-OpenRAIL.md) applies to it. By downloading and using the model you agree to the use restrictions in its Section 2; if you pass the model on, include a copy of the license. The corpus's actors gave written consent to open release and lawful use of the recordings.

The corpus authors ask to cite: I. Shigabeev, I. Latyshev. *Dialogs: A Studio-Quality Expressive Conversational Russian Speech Corpus for Dialog Assistants*. Interspeech 2026. <https://arxiv.org/abs/2607.14310>
