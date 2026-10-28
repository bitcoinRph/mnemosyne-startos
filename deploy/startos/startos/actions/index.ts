import { sdk } from '../sdk'
import { addAgentToken } from './addAgentToken'
import { connectionDetails } from './connectionDetails'
import { revokeAgentToken } from './revokeAgentToken'

export const actions = sdk.Actions.of()
  .addAction(addAgentToken)
  .addAction(revokeAgentToken)
  .addAction(connectionDetails)
