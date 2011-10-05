import ConfigParser

config = ConfigParser.RawConfigParser()

config.add_section('ServerConfig')
config.set('ServerConfig', 'BLOCK_SIZE', 2048)
config.set('ServerConfig', 'ROOT_DIR', '/tmp/')
config.set('ServerConfig', 'FRIENDS', 'http://example.com/,http://example.ca/')
config.set('ServerConfig', 'HOST_IP', '0.0.0.0')
config.set('ServerConfig', 'HOST_PORT', '8051')
config.set('ServerConfig', 'THREAD_NUM', '10')


# Writing our configuration file to 'example.cfg'
with open('annelia.conf.example', 'wb') as configfile:
    config.write(configfile)
