Rails.application.config.filter_parameters += %i[
  api_key
  token
  authorization
  private_key
  private_key_passphrase
]
