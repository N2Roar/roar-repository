# -*- coding: utf-8 -*-

'''
#:::'##::::'#######:::'######::'##::::::::'#######::'##:::::'##:'##::: ##::'######::
#:'####:::'##.... ##:'##... ##: ##:::::::'##.... ##: ##:'##: ##: ###:: ##:'##... ##:
#:.. ##:::..::::: ##: ##:::..:: ##::::::: ##:::: ##: ##: ##: ##: ####: ##: ##:::..::
#::: ##::::'#######:: ##::::::: ##::::::: ##:::: ##: ##: ##: ##: ## ## ##:. ######::
#::: ##::::...... ##: ##::::::: ##::::::: ##:::: ##: ##: ##: ##: ##. ####::..... ##:
#::: ##:::'##:::: ##: ##::: ##: ##::::::: ##:::: ##: ##: ##: ##: ##:. ###:'##::: ##:
#:'######:. #######::. ######:: ########:. #######::. ###. ###:: ##::. ##:. ######::
#:......:::.......::::......:::........:::.......::::...::...:::..::::..:::......:::

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import base64;exec base64.b64decode('CmltcG9ydCByZXF1ZXN0cyxvcyxzeXMscmUsZGF0ZXRpbWUsdXJscGFyc2UsanNvbix4Ym1jZ3VpLHhibWNwbHVnaW4KCmZyb20gcmVzb3VyY2VzLmxpYi5tb2R1bGVzIGltcG9ydCBsb2dfdXRpbHMKZnJvbSByZXNvdXJjZXMubGliLm1vZHVsZXMgaW1wb3J0IGNhY2hlCmZyb20gcmVzb3VyY2VzLmxpYi5tb2R1bGVzIGltcG9ydCBjbGllbnQKZnJvbSByZXNvdXJjZXMubGliLm1vZHVsZXMgaW1wb3J0IGNvbnRyb2wKCnN5c2FkZG9uID0gc3lzLmFyZ3ZbMF0gOyBzeXNoYW5kbGUgPSBpbnQoc3lzLmFyZ3ZbMV0pCmFydFBhdGggPSBjb250cm9sLmFydFBhdGgoKSA7IGFkZG9uRmFuYXJ0ID0gY29udHJvbC5hZGRvbkZhbmFydCgpCgpjbGFzcyBkb2N1bWVudGFyeToKICAgIGRlZiBfX2luaXRfXyhzZWxmKToKICAgICAgICBzZWxmLmxpc3QgPSBbXSAKICAgICAgICAKICAgICAgICBzZWxmLmRvY3VfbGluayA9ICdodHRwczovL3RvcGRvY3VtZW50YXJ5ZmlsbXMuY29tLycKICAgICAgICBzZWxmLmRvY3VfY2F0X2xpc3QgPSAnaHR0cHM6Ly90b3Bkb2N1bWVudGFyeWZpbG1zLmNvbS93YXRjaC1vbmxpbmUvJwoKICAgIGRlZiByb290KHNlbGYpOgogICAgICAgIHRyeToKICAgICAgICAgICAgaHRtbCA9IGNsaWVudC5yZXF1ZXN0KHNlbGYuZG9jdV9jYXRfbGlzdCkKCiAgICAgICAgICAgIGNhdF9saXN0ID0gY2xpZW50LnBhcnNlRE9NKGh0bWwsICdkaXYnLCBhdHRycz17J2NsYXNzJzonc2l0ZW1hcC13cmFwZXIgY2xlYXInfSkKICAgICAgICAgICAgZm9yIGNvbnRlbnQgaW4gY2F0X2xpc3Q6CiAgICAgICAgICAgICAgICBjYXRfaW5mbyA9IGNsaWVudC5wYXJzZURPTShjb250ZW50LCAnaDInKVswXQogICAgICAgICAgICAgICAgY2F0X3VybCA9IGNsaWVudC5wYXJzZURPTShjYXRfaW5mbywgJ2EnLCByZXQ9J2hyZWYnKVswXQogICAgICAgICAgICAgICAgY2F0X3RpdGxlID0gY2xpZW50LnBhcnNlRE9NKGNhdF9pbmZvLCAnYScpWzBdLmVuY29kZSgndXRmLTgnLCAnaWdub3JlJykuZGVjb2RlKCd1dGYtOCcpLnJlcGxhY2UoIiZhbXA7IiwiJiIpLnJlcGxhY2UoJyYjMzk7JywiJyIpLnJlcGxhY2UoJyZxdW90OycsJyInKS5yZXBsYWNlKCcmIzM5OycsIiciKS5yZXBsYWNlKCcmIzgyMTE7JywnIC0gJykucmVwbGFjZSgnJiM4MjE3OycsIiciKS5yZXBsYWNlKCcmIzgyMTY7JywiJyIpLnJlcGxhY2UoJyYjMDM4OycsJyYnKS5yZXBsYWNlKCcmYWNpcmM7JywnJykKICAgICAgICAgICAgICAgIHRyeToKICAgICAgICAgICAgICAgICAgICBjYXRfaWNvbiA9IGNsaWVudC5wYXJzZURPTShjb250ZW50LCAnaW1nJywgcmV0PSdkYXRhLXNyYycpWzBdCiAgICAgICAgICAgICAgICBleGNlcHQ6CiAgICAgICAgICAgICAgICAgICAgY2F0X2ljb24gPSBjbGllbnQucGFyc2VET00oY29udGVudCwgJ2ltZycsIHJldD0nc3JjJylbMF0KICAgICAgICAgICAgICAgIGNhdF9hY3Rpb24gPSAnZG9jdUhlYXZlbiZkb2N1Q2F0PSVzJyAlIGNhdF91cmwKICAgICAgICAgICAgICAgIHNlbGYubGlzdC5hcHBlbmQoeyduYW1lJzogY2F0X3RpdGxlLCAndXJsJzogY2F0X3VybCwgJ2ltYWdlJzogY2F0X2ljb24sICdhY3Rpb24nOiBjYXRfYWN0aW9ufSkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgICAgIGxvZ191dGlscy5sb2coJ2RvY3VtZW50YXJ5IHJvb3QgOiBFeGNlcHRpb24gLSAnICsgc3RyKGUpKQogICAgICAgICAgICBwYXNzCgogICAgICAgIHNlbGYubGlzdCA9IHNlbGYubGlzdFs6Oi0xXQogICAgICAgIHNlbGYuYWRkRGlyZWN0b3J5KHNlbGYubGlzdCkKICAgICAgICByZXR1cm4gc2VsZi5saXN0CgogICAgZGVmIGRvY3VfbGlzdChzZWxmLCB1cmwpOgogICAgICAgIHRyeToKICAgICAgICAgICAgaHRtbCA9IGNsaWVudC5yZXF1ZXN0KHVybCkKCiAgICAgICAgICAgIGNhdF9saXN0ID0gY2xpZW50LnBhcnNlRE9NKGh0bWwsICdhcnRpY2xlJywgYXR0cnM9eydjbGFzcyc6J21vZHVsZSd9KQogICAgICAgICAgICBmb3IgY29udGVudCBpbiBjYXRfbGlzdDoKICAgICAgICAgICAgICAgIGRvY3VfaW5mbyA9IGNsaWVudC5wYXJzZURPTShjb250ZW50LCAnaDInKVswXQogICAgICAgICAgICAgICAgZG9jdV91cmwgPSBjbGllbnQucGFyc2VET00oZG9jdV9pbmZvLCAnYScsIHJldD0naHJlZicpWzBdCiAgICAgICAgICAgICAgICBkb2N1X3RpdGxlID0gY2xpZW50LnBhcnNlRE9NKGRvY3VfaW5mbywgJ2EnKVswXS5yZXBsYWNlKCImYW1wOyIsIiYiKS5yZXBsYWNlKCcmIzM5OycsIiciKS5yZXBsYWNlKCcmcXVvdDsnLCciJykucmVwbGFjZSgnJiMzOTsnLCInIikucmVwbGFjZSgnJiM4MjExOycsJyAtICcpLnJlcGxhY2UoJyYjODIxNzsnLCInIikucmVwbGFjZSgnJiM4MjE2OycsIiciKS5yZXBsYWNlKCcmIzAzODsnLCcmJykucmVwbGFjZSgnJmFjaXJjOycsJycpCiAgICAgICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICAgICAgZG9jdV9pY29uID0gY2xpZW50LnBhcnNlRE9NKGNvbnRlbnQsICdpbWcnLCByZXQ9J2RhdGEtc3JjJylbMF0KICAgICAgICAgICAgICAgIGV4Y2VwdDoKICAgICAgICAgICAgICAgICAgICBkb2N1X2ljb24gPSBjbGllbnQucGFyc2VET00oY29udGVudCwgJ2ltZycsIHJldD0nc3JjJylbMF0KICAgICAgICAgICAgICAgIGRvY3VfYWN0aW9uID0gJ2RvY3VIZWF2ZW4mZG9jdVBsYXk9JXMnICUgZG9jdV91cmwKICAgICAgICAgICAgICAgIHNlbGYubGlzdC5hcHBlbmQoeyduYW1lJzogZG9jdV90aXRsZSwgJ3VybCc6IGRvY3VfdXJsLCAnaW1hZ2UnOiBkb2N1X2ljb24sICdhY3Rpb24nOiBkb2N1X2FjdGlvbn0pCgogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBuYXZpX2NvbnRlbnQgPSBjbGllbnQucGFyc2VET00oaHRtbCwgJ2RpdicsIGF0dHJzPXsnY2xhc3MnOidwYWdpbmF0aW9uIG1vZHVsZSd9KVswXQogICAgICAgICAgICAgICAgbGlua3MgPSBjbGllbnQucGFyc2VET00obmF2aV9jb250ZW50LCAnYScsIHJldD0naHJlZicpCiAgICAgICAgICAgICAgICB0bXBfbGlzdCA9IFtdCiAgICAgICAgICAgICAgICBsaW5rID0gbGlua3NbKGxlbihsaW5rcyktMSldCiAgICAgICAgICAgICAgICBkb2N1X2FjdGlvbiA9ICdkb2N1SGVhdmVuJmRvY3VDYXQ9JXMnICUgbGluawogICAgICAgICAgICAgICAgc2VsZi5saXN0LmFwcGVuZCh7J25hbWUnOiBjb250cm9sLmxhbmcoMzIwNTMpLmVuY29kZSgndXRmLTgnKSwgJ3VybCc6IGxpbmssICdpbWFnZSc6IGNvbnRyb2wuYWRkb25OZXh0KCksICdhY3Rpb24nOiBkb2N1X2FjdGlvbn0pCiAgICAgICAgICAgIGV4Y2VwdDoKICAgICAgICAgICAgICAgIHBhc3MKICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgICAgIGxvZ191dGlscy5sb2coJ2RvY3VtZW50YXJ5IGRvY3VfbGlzdCA6IEV4Y2VwdGlvbiAtICcgKyBzdHIoZSkpCiAgICAgICAgICAgIHBhc3MKCiAgICAgICAgc2VsZi5hZGREaXJlY3Rvcnkoc2VsZi5saXN0KQogICAgICAgIHJldHVybiBzZWxmLmxpc3QKCiAgICBkZWYgZG9jdV9wbGF5KHNlbGYsIHVybCk6CiAgICAgICAgdHJ5OgogICAgICAgICAgICBkb2N1X3BhZ2UgPSBjbGllbnQucmVxdWVzdCh1cmwpCiAgICAgICAgICAgIGRvY3VfaXRlbSA9IGNsaWVudC5wYXJzZURPTShkb2N1X3BhZ2UsICdtZXRhJywgYXR0cnM9eydpdGVtcHJvcCc6J2VtYmVkVXJsJ30sIHJldD0nY29udGVudCcpWzBdCiAgICAgICAgICAgIGlmICdodHRwOicgbm90IGluIGRvY3VfaXRlbSBhbmQgICdodHRwczonIG5vdCBpbiBkb2N1X2l0ZW06CiAgICAgICAgICAgICAgICBkb2N1X2l0ZW0gPSAnaHR0cHM6JyArIGRvY3VfaXRlbQogICAgICAgICAgICB1cmwgPSBkb2N1X2l0ZW0KCiAgICAgICAgICAgIGRvY3VfdGl0bGUgPSBjbGllbnQucGFyc2VET00oZG9jdV9wYWdlLCAnbWV0YScsIGF0dHJzPXsncHJvcGVydHknOidvZzp0aXRsZSd9LCByZXQ9J2NvbnRlbnQnKVswXS5lbmNvZGUoJ3V0Zi04JywgJ2lnbm9yZScpLmRlY29kZSgndXRmLTgnKS5yZXBsYWNlKCImYW1wOyIsIiYiKS5yZXBsYWNlKCcmIzM5OycsIiciKS5yZXBsYWNlKCcmcXVvdDsnLCciJykucmVwbGFjZSgnJiMzOTsnLCInIikucmVwbGFjZSgnJiM4MjExOycsJyAtICcpLnJlcGxhY2UoJyYjODIxNzsnLCInIikucmVwbGFjZSgnJiM4MjE2OycsIiciKS5yZXBsYWNlKCcmIzAzODsnLCcmJykucmVwbGFjZSgnJmFjaXJjOycsJycpCgogICAgICAgICAgICBpZiAneW91dHViZScgaW4gdXJsOgogICAgICAgICAgICAgICAgaWYgJ3ZpZGVvc2VyaWVzJyBub3QgaW4gdXJsOgogICAgICAgICAgICAgICAgICAgIHZpZGVvX2lkID0gY2xpZW50LnBhcnNlRE9NKGRvY3VfcGFnZSwgJ2RpdicsIGF0dHJzPXsnY2xhc3MnOid5b3V0dWJlLXBsYXllcid9LCByZXQ9J2RhdGEtaWQnKVswXQogICAgICAgICAgICAgICAgICAgIHVybCA9ICdwbHVnaW46Ly9wbHVnaW4udmlkZW8ueW91dHViZS9wbGF5Lz92aWRlb19pZD0lcycgJSB2aWRlb19pZAogICAgICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgICAgICBwYXNzCiAgICAgICAgICAgIGVsaWYgJ2RhaWx5bW90aW9uJyBpbiB1cmw6CiAgICAgICAgICAgICAgICB2aWRlb19pZCA9IGNsaWVudC5wYXJzZURPTShkb2N1X3BhZ2UsICdkaXYnLCBhdHRycz17J2NsYXNzJzoneW91dHViZS1wbGF5ZXInfSwgcmV0PSdkYXRhLWlkJylbMF0KICAgICAgICAgICAgICAgIHVybCA9IHNlbGYuZ2V0RGFpbHlNb3Rpb25TdHJlYW0odmlkZW9faWQpCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICBsb2dfdXRpbHMubG9nKCdQbGF5IERvY3VtZW50YXJ5OiBVbmtub3duIEhvc3Q6ICcgKyBzdHIodXJsKSkKICAgICAgICAgICAgICAgIGNvbnRyb2wuaW5mb0RpYWxvZygnVW5rbm93biBIb3N0IC0gUmVwb3J0IFRvIERldmVsb3BlcjogJyArIHN0cih1cmwpLCBzb3VuZD1UcnVlLCBpY29uPSdJTkZPJykKCiAgICAgICAgICAgIGNvbnRyb2wuZXhlY3V0ZSgnUGxheU1lZGlhKCVzKScgJSB1cmwpCgojICAgICAgICAgICAgaXRlbSA9IHhibWNndWkuTGlzdEl0ZW0oc3RyKGRvY3VfdGl0bGUpLCBpY29uSW1hZ2U9J0RlZmF1bHRWaWRlby5wbmcnLCB0aHVtYm5haWxJbWFnZT0nRGVmYXVsdFZpZGVvLnBuZycpCiMgICAgICAgICAgICBpdGVtLnNldEluZm8odHlwZT0nVmlkZW8nLCBpbmZvTGFiZWxzPXsnVGl0bGUnOiBzdHIoZG9jdV90aXRsZSksICdQbG90Jzogc3RyKGRvY3VfdGl0bGUpfSkKIyAgICAgICAgICAgIGl0ZW0uc2V0UHJvcGVydHkoJ0lzUGxheWFibGUnLCd0cnVlJykKIyAgICAgICAgICAgIGl0ZW0uc2V0UGF0aCh1cmwpCiMgICAgICAgICAgICBjb250cm9sLnJlc29sdmUoaW50KHN5cy5hcmd2WzFdKSwgVHJ1ZSwgaXRlbSkKICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGU6CiAgICAgICAgICAgIGxvZ191dGlscy5sb2coJ2RvY3VfcGxheTogRXhjZXB0aW9uIC0gJyArIHN0cihlKSkKICAgICAgICAgICAgcGFzcwoKICAgIGRlZiBzb3J0X2tleShzZWxmLCBlbGVtKToKICAgICAgICBpZiBlbGVtWzBdID09ICJhdXRvIjoKICAgICAgICAgICAgcmV0dXJuIDEKICAgICAgICBlbHNlOgogICAgICAgICAgICByZXR1cm4gaW50KGVsZW1bMF0uc3BsaXQoIkAiKVswXSkKCiAgICAjIENvZGUgb3JpZ2luYWxseSB3cml0dGVuIGJ5IGd1amFsLCBhcyBwYXJ0IG9mIHRoZSBEYWlseU1vdGlvbiBBZGRvbiBpbiB0aGUgb2ZmaWNpYWwgS29kaSBSZXBvLiBNb2RpZmllZCB0byBmaXQgdGhlIG5lZWRzIGhlcmUuCiAgICBkZWYgZ2V0RGFpbHlNb3Rpb25TdHJlYW0oc2VsZiwgaWQpOgogICAgICAgIGhlYWRlcnMgPSB7J1VzZXItQWdlbnQnOidBbmRyb2lkJ30KICAgICAgICBjb29raWUgPSB7J0Nvb2tpZSc6Imxhbmc9ZW5fVVM7IGZmPW9mZiJ9CiAgICAgICAgciA9IHJlcXVlc3RzLmdldCgiaHR0cDovL3d3dy5kYWlseW1vdGlvbi5jb20vcGxheWVyL21ldGFkYXRhL3ZpZGVvLyIraWQsaGVhZGVycz1oZWFkZXJzLGNvb2tpZXM9Y29va2llKQogICAgICAgIGNvbnRlbnQgPSByLmpzb24oKQogICAgICAgIGlmIGNvbnRlbnQuZ2V0KCdlcnJvcicpIGlzIG5vdCBOb25lOgogICAgICAgICAgICBFcnJvciA9IChjb250ZW50WydlcnJvciddWyd0aXRsZSddKQogICAgICAgICAgICB4Ym1jLmV4ZWN1dGVidWlsdGluKCdYQk1DLk5vdGlmaWNhdGlvbihJbmZvOiwnKyBFcnJvciArJyAsNTAwMCknKQogICAgICAgICAgICByZXR1cm4KICAgICAgICBlbHNlOgogICAgICAgICAgICBjYz0gY29udGVudFsncXVhbGl0aWVzJ10KCiAgICAgICAgICAgIGNjID0gY2MuaXRlbXMoKQoKICAgICAgICAgICAgY2MgPSBzb3J0ZWQoY2Msa2V5PXNlbGYuc29ydF9rZXkscmV2ZXJzZT1UcnVlKQogICAgICAgICAgICBtX3VybCA9ICcnCiAgICAgICAgICAgIG90aGVyX3BsYXlhYmxlX3VybCA9IFtdCgogICAgICAgICAgICBmb3Igc291cmNlLGpzb25fc291cmNlIGluIGNjOgogICAgICAgICAgICAgICAgc291cmNlID0gc291cmNlLnNwbGl0KCJAIilbMF0KICAgICAgICAgICAgICAgIGZvciBpdGVtIGluIGpzb25fc291cmNlOgogICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgbV91cmwgPSBpdGVtLmdldCgndXJsJyxOb25lKQoKICAgICAgICAgICAgICAgICAgICBpZiBtX3VybDoKICAgICAgICAgICAgICAgICAgICAgICAgaWYgc291cmNlID09ICJhdXRvIiA6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBjb250aW51ZQoKICAgICAgICAgICAgICAgICAgICAgICAgZWxpZiAgaW50KHNvdXJjZSkgPD0gMiA6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBpZiAndmlkZW8nIGluIGl0ZW0uZ2V0KCd0eXBlJyxOb25lKToKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICByZXR1cm4gbV91cmwKCiAgICAgICAgICAgICAgICAgICAgICAgIGVsaWYgJy5tbmZ0JyBpbiBtX3VybDoKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgICAgICAgICAgICAgIG90aGVyX3BsYXlhYmxlX3VybC5hcHBlbmQobV91cmwpCiAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICBpZiBsZW4ob3RoZXJfcGxheWFibGVfdXJsKSA+MDogIyBwcm9iYWJseSBub3QgbmVlZGVkLCBvbmx5IGZvciBsYXN0IHJlc29ydAogICAgICAgICAgICAgICAgZm9yIG1fdXJsIGluIG90aGVyX3BsYXlhYmxlX3VybDoKCiAgICAgICAgICAgICAgICAgICAgaWYgJy5tM3U4P2F1dGgnIGluIG1fdXJsOgogICAgICAgICAgICAgICAgICAgICAgICByciA9IHJlcXVlc3RzLmdldChtX3VybCxjb29raWVzPXIuY29va2llcy5nZXRfZGljdCgpICxoZWFkZXJzPWhlYWRlcnMpCiAgICAgICAgICAgICAgICAgICAgICAgIGlmIHJyLmhlYWRlcnMuZ2V0KCdzZXQtY29va2llJyk6CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBwcmludCAnYWRkaW5nIGNvb2tpZSB0byB1cmwnCiAgICAgICAgICAgICAgICAgICAgICAgICAgICBzdHJ1cmwgPSByZS5maW5kYWxsKCcoaHR0cC4rKScscnIudGV4dClbMF0uc3BsaXQoJyNjZWxsJylbMF0rJ3xDb29raWU9Jytyci5oZWFkZXJzWydzZXQtY29va2llJ10KICAgICAgICAgICAgICAgICAgICAgICAgZWxzZToKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHN0cnVybCA9IHJlLmZpbmRhbGwoJyhodHRwLispJyxyci50ZXh0KVswXS5zcGxpdCgnI2NlbGwnKVswXQogICAgICAgICAgICAgICAgICAgICAgICByZXR1cm4gc3RydXJsCgogICAgZGVmIGFkZERpcmVjdG9yeUl0ZW0oc2VsZiwgbmFtZSwgcXVlcnksIHRodW1iLCBpY29uLCBjb250ZXh0PU5vbmUsIHF1ZXVlPUZhbHNlLCBpc0FjdGlvbj1UcnVlLCBpc0ZvbGRlcj1UcnVlKToKICAgICAgICB0cnk6IG5hbWUgPSBjb250cm9sLmxhbmcobmFtZSkuZW5jb2RlKCd1dGYtOCcpCiAgICAgICAgZXhjZXB0OiBwYXNzCiAgICAgICAgdXJsID0gJyVzP2FjdGlvbj0lcycgJSAoc3lzYWRkb24sIHF1ZXJ5KSBpZiBpc0FjdGlvbiA9PSBUcnVlIGVsc2UgcXVlcnkKICAgICAgICB0aHVtYiA9IG9zLnBhdGguam9pbihhcnRQYXRoLCB0aHVtYikgaWYgbm90IGFydFBhdGggPT0gTm9uZSBlbHNlIGljb24KICAgICAgICBjbSA9IFtdCiAgICAgICAgaWYgcXVldWUgPT0gVHJ1ZTogY20uYXBwZW5kKChxdWV1ZU1lbnUsICdSdW5QbHVnaW4oJXM/YWN0aW9uPXF1ZXVlSXRlbSknICUgc3lzYWRkb24pKQogICAgICAgIGlmIG5vdCBjb250ZXh0ID09IE5vbmU6IGNtLmFwcGVuZCgoY29udHJvbC5sYW5nKGNvbnRleHRbMF0pLmVuY29kZSgndXRmLTgnKSwgJ1J1blBsdWdpbiglcz9hY3Rpb249JXMpJyAlIChzeXNhZGRvbiwgY29udGV4dFsxXSkpKQogICAgICAgIGl0ZW0gPSBjb250cm9sLml0ZW0obGFiZWw9bmFtZSkKICAgICAgICBpdGVtLmFkZENvbnRleHRNZW51SXRlbXMoY20pCiAgICAgICAgaXRlbS5zZXRBcnQoeydpY29uJzogdGh1bWIsICd0aHVtYic6IHRodW1ifSkKICAgICAgICBpZiBub3QgYWRkb25GYW5hcnQgPT0gTm9uZTogaXRlbS5zZXRQcm9wZXJ0eSgnRmFuYXJ0X0ltYWdlJywgYWRkb25GYW5hcnQpCiAgICAgICAgY29udHJvbC5hZGRJdGVtKGhhbmRsZT1zeXNoYW5kbGUsIHVybD11cmwsIGxpc3RpdGVtPWl0ZW0sIGlzRm9sZGVyPWlzRm9sZGVyKQoKICAgIGRlZiBlbmREaXJlY3Rvcnkoc2VsZik6CiAgICAgICAgY29udHJvbC5jb250ZW50KHN5c2hhbmRsZSwgJ2FkZG9ucycpCiAgICAgICAgY29udHJvbC5kaXJlY3Rvcnkoc3lzaGFuZGxlLCBjYWNoZVRvRGlzYz1UcnVlKQoKICAgIGRlZiBhZGREaXJlY3Rvcnkoc2VsZiwgaXRlbXMsIHF1ZXVlPUZhbHNlLCBpc0ZvbGRlcj1UcnVlKToKICAgICAgICBpZiBpdGVtcyA9PSBOb25lIG9yIGxlbihpdGVtcykgPT0gMDogY29udHJvbC5pZGxlKCkgOyBzeXMuZXhpdCgpCgogICAgICAgIHN5c2FkZG9uID0gc3lzLmFyZ3ZbMF0KCiAgICAgICAgc3lzaGFuZGxlID0gaW50KHN5cy5hcmd2WzFdKQoKICAgICAgICBhZGRvbkZhbmFydCwgYWRkb25UaHVtYiwgYXJ0UGF0aCA9IGNvbnRyb2wuYWRkb25GYW5hcnQoKSwgY29udHJvbC5hZGRvblRodW1iKCksIGNvbnRyb2wuYXJ0UGF0aCgpCgogICAgICAgIHF1ZXVlTWVudSA9IGNvbnRyb2wubGFuZygzMjA2NSkuZW5jb2RlKCd1dGYtOCcpCgogICAgICAgIHBsYXlSYW5kb20gPSBjb250cm9sLmxhbmcoMzI1MzUpLmVuY29kZSgndXRmLTgnKQoKICAgICAgICBhZGRUb0xpYnJhcnkgPSBjb250cm9sLmxhbmcoMzI1NTEpLmVuY29kZSgndXRmLTgnKQoKICAgICAgICBmb3IgaSBpbiBpdGVtczoKICAgICAgICAgICAgdHJ5OgogICAgICAgICAgICAgICAgbmFtZSA9IGlbJ25hbWUnXQoKICAgICAgICAgICAgICAgIGlmIGlbJ2ltYWdlJ10uc3RhcnRzd2l0aCgnaHR0cCcpOiB0aHVtYiA9IGlbJ2ltYWdlJ10KICAgICAgICAgICAgICAgIGVsaWYgbm90IGFydFBhdGggPT0gTm9uZTogdGh1bWIgPSBvcy5wYXRoLmpvaW4oYXJ0UGF0aCwgaVsnaW1hZ2UnXSkKICAgICAgICAgICAgICAgIGVsc2U6IHRodW1iID0gYWRkb25UaHVtYgoKICAgICAgICAgICAgICAgIGl0ZW0gPSBjb250cm9sLml0ZW0obGFiZWw9bmFtZSkKCiAgICAgICAgICAgICAgICBpZiBpc0ZvbGRlcjoKICAgICAgICAgICAgICAgICAgICB1cmwgPSAnJXM/YWN0aW9uPSVzJyAlIChzeXNhZGRvbiwgaVsnYWN0aW9uJ10pCiAgICAgICAgICAgICAgICAgICAgdHJ5OiB1cmwgKz0gJyZ1cmw9JXMnICUgdXJsbGliLnF1b3RlX3BsdXMoaVsndXJsJ10pCiAgICAgICAgICAgICAgICAgICAgZXhjZXB0OiBwYXNzCiAgICAgICAgICAgICAgICAgICAgaXRlbS5zZXRQcm9wZXJ0eSgnSXNQbGF5YWJsZScsICdmYWxzZScpCiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgIHVybCA9ICclcz9hY3Rpb249JXMnICUgKHN5c2FkZG9uLCBpWydhY3Rpb24nXSkKICAgICAgICAgICAgICAgICAgICB0cnk6IHVybCArPSAnJnVybD0lcycgJSBpWyd1cmwnXQogICAgICAgICAgICAgICAgICAgIGV4Y2VwdDogcGFzcwogICAgICAgICAgICAgICAgICAgIGl0ZW0uc2V0UHJvcGVydHkoJ0lzUGxheWFibGUnLCAndHJ1ZScpCiAgICAgICAgICAgICAgICAgICAgaXRlbS5zZXRJbmZvKCJtZWRpYXR5cGUiLCAidmlkZW8iKQogICAgICAgICAgICAgICAgICAgIGl0ZW0uc2V0SW5mbygiYXVkaW8iLCAnJykKCiAgICAgICAgICAgICAgICBpdGVtLnNldEFydCh7J2ljb24nOiB0aHVtYiwgJ3RodW1iJzogdGh1bWJ9KQogICAgICAgICAgICAgICAgaWYgbm90IGFkZG9uRmFuYXJ0ID09IE5vbmU6IGl0ZW0uc2V0UHJvcGVydHkoJ0ZhbmFydF9JbWFnZScsIGFkZG9uRmFuYXJ0KQoKICAgICAgICAgICAgICAgIGNvbnRyb2wuYWRkSXRlbShoYW5kbGU9c3lzaGFuZGxlLCB1cmw9dXJsLCBsaXN0aXRlbT1pdGVtLCBpc0ZvbGRlcj1pc0ZvbGRlcikKICAgICAgICAgICAgZXhjZXB0OgogICAgICAgICAgICAgICAgcGFzcwoKICAgICAgICBjb250cm9sLmNvbnRlbnQoc3lzaGFuZGxlLCAnYWRkb25zJykKICAgICAgICBjb250cm9sLmRpcmVjdG9yeShzeXNoYW5kbGUsIGNhY2hlVG9EaXNjPVRydWUp')