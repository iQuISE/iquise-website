import json, os, django, datetime
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iquise.settings")
django.setup()

from iquhack.models import *

Hackathon.objects.all().delete()
hackathon = Hackathon(start_date = datetime.date(2021, 1, 29),
end_date = datetime.date(2021, 1, 31),
back_drop_image = "background_highres.png",
published = True,
opens = datetime.datetime.now(),
deadline = datetime.date(2021, 1, 28)
)
hackathon.save()

with open("data2020.json") as fid:
    dat = json.load(fid)

Tier.objects.all().delete()
for i, tier in enumerate(dat["Tier"]):
    Tier(index=i, logo_rel_size=tier["logo_rel_size"]).save()

FAQ.objects.all().delete()
for i, FAQi in enumerate(dat["FAQ"]):
    f = FAQ(question=FAQi["question"], answer=FAQi["answer"])
    f.save()
    UsedFAQ(hackathon=hackathon, FAQ=f, index=i).save()

Sponsor.objects.all().delete()
for s in dat["Sponsor"]:
    spons = Sponsor(name=s["name"], logo=s["logo"], link=s["link"])
    spons.save()
    Sponsorship(hackathon=hackathon, sponsor=spons, tier=Tier.objects.filter(index=s["tier"]-1).first(), platform = s["hardware"], agreement="").save()

Section.objects.all().delete()
for i, s in enumerate(dat["Section"]):
    sec = Section(title=s["title"], content=s["content"])
    sec.save()
    UsedSection(hackathon=hackathon, section=sec, index=i).save()