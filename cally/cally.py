import configparser
import requests
import click
import xdg
import dateutil.parser

API_ENDPOINT = 'https://calendly.com/api/v1/'
CONFIG_FILE = xdg.XDG_CONFIG_HOME/'cally.conf'

conf = configparser.ConfigParser(default_section=None)
conf.read(CONFIG_FILE)

TOKEN = conf['cally']['token']

class ApiObject(dict):
    def __init__(self, json, incs=None):
        self.type = json['type']
        self.id = json['id']
        self.update(json['attributes'])

        if incs is not None:
            for rname, rdata in json.get('relationships', {}).items():
                rtype, rid = rdata['data']['type'], rdata['data']['id']
                try:
                    self.__dict__[rname] = incs[rtype, rid]
                except KeyError:
                    pass


    def __repr__(self):
        s = self.type + '<' + self.id + '> ' + dict.__repr__(self)
        return s

def get(path, *args, **kwargs):
    kwargs.setdefault('headers', dict())
    kwargs['headers'].setdefault('X-TOKEN', TOKEN)
    js = requests.get(API_ENDPOINT + path, *args, **kwargs).json()
    data = js['data']

    incs = {}
    for inc in map(ApiObject, js.get('included', [])):
        incs[inc.type, inc.id] = inc
    if isinstance(data, list):
        return [ApiObject(item, incs) for item in data]
    else:
        return ApiObject(data, incs)

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        user()

@main.command()
def user():
    user = get('users/me')
    click.echo(f'{user["name"]} <{user["email"]}>')

@main.command()
def events():
    evts = get('users/me/events', params={'include': 'event_type,invitee'})
    for evt in sorted(evts, key=lambda e: e['start_time']):
        startdt = dateutil.parser.parse(evt['start_time']).astimezone() 
        enddt = dateutil.parser.parse(evt['end_time']).astimezone() 
        startdate = startdt.strftime('%a %d')
        starttime = startdt.strftime('%H:%M')
        endtime = enddt.strftime('%H:%M')
        click.echo(f'{startdate} {starttime}-{endtime}\n   {evt.event_type["name"]} with {evt.invitee["name"]} <{evt.invitee["email"]}>')
