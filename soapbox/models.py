#!/usr/bin/python
#
# Data model for Soapbox call banking tool
# Author: Steve Salevan (steve.salevan@gmail.com)

from django.contrib.gis.db import models
from django.contrib.localflavor.us.models import USStateField

CALL_STATE = (
  ('Q', 'queued'),
  ('R', 'ringing'),
  ('I', 'in-progress'),
  ('C', 'completed'),
  ('B', 'busy'),
  ('F', 'failed'),
  ('N', 'no-answer'),
  ('X', 'canceled'),
  ('U', 'uncalled'),
)


class User(models.Model):
  """Soapbox user."""

  full_name = models.CharField(max_length=100)
  username = models.CharField(max_length=50)
  password = models.CharField(max_length=50)
  account_sid = models.CharField(max_length=50)
  auth_token = models.CharField(max_length=50)
  profile_text = models.TextField()
  city = models.CharField(max_length=50)
  state = USStateField()

  def __unicode__(self):
    return self.username


class OwnedObject(models.Model):
  """Object which is owned."""

  VISIBILITY = (
    ('G', 'GROUP'),
    ('P', 'PUBLIC'),
    ('R', 'PRIVATE'),
  )
  active = models.BooleanField(default=True)
  timestamp = models.DateTimeField(auto_now=True)
  owner = models.ForeignKey(User)
  group = models.ForeignKey('Group')
  visibility = models.CharField(max_length=1,
      choices = VISIBILITY)

  class Meta:
    abstract = True


class Group(models.Model):
  """Soapbox collaboration group."""

  administrators = models.OneToManyField(User)
  description = models.TextField()
  members = models.ManyToManyField(User)
  moderators = models.ManyToManyField(User)
  name = models.CharField(max_length=50)
  url = models.CharField(max_length=100)


class OwnedShareableObject(OwnedObject):
  """Object which may be shared."""

  edit_groups = models.ManyToMany(Group)
  edit_users = models.ManyToMany(User)
  name = models.CharField(max_length=100)
  view_groups = models.ManyToMany(Group)
  view_users = models.ManyToMany(User)

  class Meta:
    abstract = True
    ordering = ['name']


class Campaign(OwnedShareableObject):
  """Contains a phone banking campaign."""

  description = models.TextField()
  script = models.ForeignKey(Script)
  targets = models.ManyToManyField(Region)


class Call(models.Model):
  """Record of a call made through Soapbox."""

  campaign = models.ForeignKey(Campaign)
  to_number = models.CharField(max_length=20)
  from_number = models.ForeignKey(Number)
  duration = models.IntegerField()
  results = models.ManyToManyField(Result)


class Number(OwnedObject):
  """Outbound phone number held by a user."""

  POOLING_STATE = (
    ('I', 'in-pool'),
    ('O', 'out-of-pool'),
  )
  state = models.CharField(max_length=1,
      choices = CALL_STATE)
  pooling = models.CharField(max_length=1,
      choices = POOLING_STATE)
  number = models.CharField(max_length=50)


class Result(OwnedObject):
  """Contains a single result object."""

  outcome = models.CharField(max_length=1,
      choices = CALL_STATE, default = 'U')
  campaign = models.ForeignKey(Campaign)
  from_number = models.ForeignKey(Number)
  latlon = models.PointField()
  timestamp = models.DateField(auto_now=True)
  to_number = models.CharField(max_length=20)
  question = models.ForeignKey(Question)
  result = models.CharField()


class Script(OwnedShareableObject):
  description = models.TextField()
  questions = models.CharField()


class Question(OwnedObject):
  """Contains a post-call survey question."""

  QUESTION_TYPE = (
    ('C', 'CHECKBOX'),
    ('D', 'DROPDOWN'),
    ('R', 'RADIO'),
    ('S', 'SHORTFORM'),
    ('L', 'LONGFORM'),
  )
  prompts = models.TextField() # stores prompts protobuf
  text = models.TextField()
  type = models.CharField(length=1, choices=QUESTION_TYPE)


class Prompt(OwnedShareableObject):
  """Contains a question prompt."""

  text = models.CharField()


class NumberRange(models.Model):
  """Contains a range of numbers associated with a region."""

  number_range = models.CharField(max_length=100)
  region = models.ForeignKey(Region)


class Region(models.Model):
  """Contains a geographical region."""

  name = models.CharField(max_length=100)
  state = USStateField()
  bounds = models.PolygonField()
  objects = models.GeoManager() # needed for querying
