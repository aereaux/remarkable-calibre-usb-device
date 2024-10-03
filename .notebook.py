# https://github.com/404Wolf/remarkable-connection-utility/tree/0dc42d188af723569a07f827b43713e9c56ef6c7
# https://github.com/cherti/remarkable-cli-tooling/blob/4876f3cecbd6c2365441e24ec4d113d613159362/resync.py#L12
# https://github.com/sergei-mironov/remarkable-cli-tooling/tree/ceccaf4b2c30fcbaad0a7f3397147763c0e35f5e
# %%
import rm_ssh

IP="10.11.99.1"
rm_ssh.mkdir(IP, "test_andri", "")
rm_ssh.xochitl_restart(IP)
# %%
import rm_web_interface

# %%

rm_web_interface.upload_file("xxx.pdf", r"C:\Users\andri\Downloads\Fiche abonnement.pdf")
rm_web_interface.upload_file("Ficheabonnement.pdf", r"C:\Users\andri\Downloads\Fiche abonnement.pdf")
# %%
