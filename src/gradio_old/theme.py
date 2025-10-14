"""Theme and styling configuration for the Gradio interface."""

from gradio.themes import Soft
from gradio.themes.utils import colors, fonts, sizes

# Define the Thistle color palette
colors.thistle = colors.Color(
    name="thistle",
    c50="#F9F5F9",
    c100="#F0E8F1",
    c200="#E7DBE8",
    c300="#DECEE0",
    c400="#D2BFD8",
    c500="#D8BFD8",  # Thistle base color
    c600="#B59CB7",
    c700="#927996",
    c800="#6F5675",
    c900="#4C3454",
    c950="#291233",
)

colors.red_gray = colors.Color(
    name="red_gray",
    c50="#f7eded",
    c100="#f5dcdc",
    c200="#efb4b4",
    c300="#e78f8f",
    c400="#d96a6a",
    c500="#c65353",
    c600="#b24444",
    c700="#8f3434",
    c800="#732d2d",
    c900="#5f2626",
    c950="#4d2020",
)


class ThistleTheme(Soft):
    """Custom Thistle theme for the Gradio interface."""

    def __init__(
        self,
        *,
        primary_hue: colors.Color | str = colors.gray,
        secondary_hue: colors.Color | str = colors.thistle,  # Use the new color
        neutral_hue: colors.Color | str = colors.slate,
        text_size: sizes.Size | str = sizes.text_lg,
        font: fonts.Font | str | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("Outfit"),
            "Arial",
            "sans-serif",
        ),
        font_mono: fonts.Font | str | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("IBM Plex Mono"),
            "ui-monospace",
            "monospace",
        ),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            text_size=text_size,
            font=font,
            font_mono=font_mono,
        )
        super().set(
            background_fill_primary="*primary_50",
            background_fill_primary_dark="*primary_900",
            body_background_fill="linear-gradient(135deg, *primary_200, *primary_100)",
            body_background_fill_dark="linear-gradient(135deg, *primary_900, *primary_800)",
            button_primary_text_color="black",
            button_primary_text_color_hover="white",
            button_primary_background_fill="linear-gradient(90deg, *secondary_400, *secondary_500)",
            button_primary_background_fill_hover="linear-gradient(90deg, *secondary_500, *secondary_600)",
            button_primary_background_fill_dark="linear-gradient(90deg, *secondary_600, *secondary_700)",
            button_primary_background_fill_hover_dark="linear-gradient(90deg, *secondary_500, *secondary_600)",
            button_secondary_text_color="black",
            button_secondary_text_color_hover="white",
            button_secondary_background_fill="linear-gradient(90deg, *primary_300, *primary_300)",
            button_secondary_background_fill_hover="linear-gradient(90deg, *primary_400, *primary_400)",
            button_secondary_background_fill_dark="linear-gradient(90deg, *primary_500, *primary_600)",
            button_secondary_background_fill_hover_dark="linear-gradient(90deg, *primary_500, *primary_500)",
            slider_color="*secondary_400",
            slider_color_dark="*secondary_600",
            block_title_text_weight="600",
            block_border_width="3px",
            block_shadow="*shadow_drop_lg",
            button_primary_shadow="*shadow_drop_lg",
            button_large_padding="11px",
            color_accent_soft="*primary_100",
            block_label_background_fill="*primary_200",
        )


# Instantiate the new theme
thistle_theme = ThistleTheme()


css = """
#main-title h1 {
    font-size: 2.3em !important;
}
#output-title h2 {
    font-size: 2.1em !important;
}
:root {
    --color-grey-50: #f9fafb;
    --banner-background: var(--secondary-400);
    --banner-text-color: var(--primary-100);
    --banner-background-dark: var(--secondary-800);
    --banner-text-color-dark: var(--primary-100);
    --banner-chrome-height: calc(16px + 43px);
    --chat-chrome-height-wide-no-banner: 320px;
    --chat-chrome-height-narrow-no-banner: 450px;
    --chat-chrome-height-wide: calc(var(--chat-chrome-height-wide-no-banner) + var(--banner-chrome-height));
    --chat-chrome-height-narrow: calc(var(--chat-chrome-height-narrow-no-banner) + var(--banner-chrome-height));
}
.banner-message { background-color: var(--banner-background); padding: 5px; margin: 0; border-radius: 5px; border: none; }
.banner-message-text { font-size: 13px; font-weight: bolder; color: var(--banner-text-color) !important; }
body.dark .banner-message { background-color: var(--banner-background-dark) !important; }
body.dark .gradio-container .contain .banner-message .banner-message-text { color: var(--banner-text-color-dark) !important; }
.toast-body { background-color: var(--color-grey-50); }
.html-container:has(.css-styles) { padding: 0; margin: 0; }
.css-styles { height: 0; }
.model-message { text-align: end; }
.model-dropdown-container { display: flex; align-items: center; gap: 10px; padding: 0; }
.user-input-container .multimodal-textbox{ border: none !important; }
.control-button { height: 51px; }
button.cancel { border: var(--button-border-width) solid var(--button-cancel-border-color); background: var(--button-cancel-background-fill); color: var(--button-cancel-text-color); box-shadow: var(--button-cancel-shadow); }
button.cancel:hover, .cancel[disabled] { background: var(--button-cancel-background-fill-hover); color: var(--button-cancel-text-color-hover); }
.opt-out-message { top: 8px; }
.opt-out-message .html-container, .opt-out-checkbox label { font-size: 14px !important; padding: 0 !important; margin: 0 !important; color: var(--neutral-400) !important; }
div.block.chatbot { height: calc(100svh - var(--chat-chrome-height-wide)) !important; max-height: 900px !important; }
div.no-padding { padding: 0 !important; }
@media (max-width: 1280px) { div.block.chatbot { height: calc(100svh - var(--chat-chrome-height-wide)) !important; } }
@media (max-width: 1024px) {
    .responsive-row { flex-direction: column; }
    .model-message { text-align: start; font-size: 10px !important; }
    .model-dropdown-container { flex-direction: column; align-items: flex-start; }
    div.block.chatbot { height: calc(100svh - var(--chat-chrome-height-narrow)) !important; }
}
@media (max-width: 400px) {
    .responsive-row { flex-direction: column; }
    .model-message { text-align: start; font-size: 10px !important; }
    .model-dropdown-container { flex-direction: column; align-items: flex-start; }
    div.block.chatbot { max-height: 360px !important; }
}
@media (max-height: 932px) { .chatbot { max-height: 500px !important; } }
@media (max-height: 1280px) { div.block.chatbot { max-height: 800px !important; }
"""
