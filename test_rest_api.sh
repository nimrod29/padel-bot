#!/bin/bash

# Test script for REST API fallback
# This sets the environment variables and runs a single check

echo "🎾 Testing Padel Israel REST API"
echo "================================"

# Set the authentication headers from your browser
export PADEL_ISRAEL_COOKIE="_ga=GA1.1.1016457568.1763290682; intercom-id-u1mtnxxh=6fb62dac-c33c-4798-bbe0-b5fdf1f49eae; intercom-device-id-u1mtnxxh=b0aaa979-189a-4595-b6fb-7f12dbf78676; cf_clearance=YMJpbmRFEwgszjWyGD4MtQomtRvmfZScdicXSgpprjk-1763290685-1.2.1.1-a6EVaY7G0dYLlPpRoEBwHaRHItxluFl1j9kCIEMvaLMLRht9wkd1yNkc8CNg.InPh5d6RashnaO5XVCZlEdn9rowGeMj0rnzvXxD9fWO.k4eBXBw1zczM0lwN4WcmIACE2vdabizaXkMOhhyyn0XwICrzbIqjm6OjQ0ExrNh4eSVhWn9w6ItU3CJ9jm3ZH7wwRQYlp1jtet7YNDScTzPCJgKbadjMbFa7hyfaWn7EE6My_BkacB8h7fsL4_lX7w2; __stripe_mid=e4ceacce-5155-454a-9555-155ee87547f51c4273; __stripe_sid=b8b7c259-9ad8-4e23-8b44-158129774d648ea1f2; aws-waf-token=8cb9a041-c91e-4ab3-a72d-199dfc9625d6:EQoAnSBLhySYAAAA:ejQKxMWWi7ebBVkFw5FoIMwsuePb/74bdG99rW9FvB/GhcPIdYQ+Q3V8X/xL3ZhRsFjYqeaQUpxfb/EHjn5sHUhuxVDLun/xqJben4Jia2hnsk28FCqcXonZhyk/VbbIRo8mXxPlUNHHrBimLhfPdHNOHs7NR0WPGNgKVSeoCkgD3Ri1VVSoX2Qh6XB/3AYICAIZrkxTEZgN54dm3O5xikVvo0VXNjnYo6KzIZInUvezer3B4j36hUL9uIKMgKiydg==; _gcl_au=1.1.1620318633.1763290683.1357337420.1763290696.1763290726; _ga_M060445B8S=GS2.1.s1763290682\$o1\$g1\$t1763290727\$j15\$l0\$h0; intercom-session-u1mtnxxh=TWhsUkU3TUFrS21Xcks2cXFvWDJoc1BZL1RyVHRxM2ZQdDhZS1N6am9iUDd2MlhVcjdYdU53VkVDbzVzOFJzWEJkQ2RUUm4xRFdGa2FXaVcvLzlrb2hGT1BPZHVROUtBT1Q3OXpob0FvMVk9LS1QamlESGZCcHVuZXZUVUlsZlpNUU1BPT0=--364a85d3fa9130892dedc81290cbb021389882e4; _paybycourt_session=VvL4fuWBYMfr9mgHhvsQ52uWYeX2T%2Foxa8%2B4Ru2Oq1UUmJjf%2F0H0B27Yq%2FLrSO246IPjyu1d%2F3WpWdvU%2BHZsP9r0Bn8muzlf9Z4E%2BaPYt1gGZPqcSLs%2BRY6x2qcgAzk1ykBta9SO3Tol58AziyYoLXEaL4mMDU5w81ZzGma7D6g1Q2xIXgUpmbKKRWb2DaCylIZJx8ES1jO9NULYVbmWcAke0mQ0ldFGC762FZtvBFiGKSjjWt4bwiNOoOMSOihMxx8Z2YN9XAV8EmJpaZDIcN%2FEWEYGnhkVahg2LxbCkqbI4jg15rTlPHkgW4KjXCGN%2BYBerdu%2By9FfxuiwXUdRokaSctPr1hQNsO%2B4Hlerufvw8DItqgMzjd8eiRoFecL76O3wgZlXdDCebiWf93XFFp7TxMjI%2Bfk9NnB37IGq57i6G6QZgCMXor3kQO%2B9Y6GS9gqWljF1BXOU8F4O1bn73rOf460Tn8FhK4H6ijtS9g%3D%3D--eg0aXHX7HWhO9IZp--rhH%2FNraiIhPncC7un9rYmA%3D%3D"

export PADEL_ISRAEL_CSRF_TOKEN="ajVZk1wMymA3lYJfGExDY5XVKT-EXHHF4A-9K5xA28L3xHbOjTOInl-YDKeqqk6XyX8E4LZ8P6i6TwWDrkNI0w"

# Telegram credentials
export TELEGRAM_BOT_TOKEN="7586648733:AAEsyD-NcKxK1kZu_z-k1xPCs6meg7lZ14o"
export TELEGRAM_CHAT_ID="-4824881171"

echo "✅ Environment variables set"
echo ""
echo "Running single mode check..."
echo "Press Ctrl+C to stop"
echo ""

# Activate virtual environment and run
source .venv/bin/activate
python main.py --mode single

echo ""
echo "✅ Test complete!"


