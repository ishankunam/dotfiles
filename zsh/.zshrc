# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

export EDITOR="code --wait"
export VISUAL="code --wait"

ZSH_THEME="powerlevel10k/powerlevel10k"

# Standard plugins live in $ZSH/plugins/, custom ones in $ZSH_CUSTOM/plugins/.
# Add wisely, as too many plugins slow down shell startup.
plugins=(git zsh-autosuggestions zsh-syntax-highlighting web-search)

source $ZSH/oh-my-zsh.sh

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
eval "$(rbenv init - zsh)"
export SSH_AUTH_SOCK=$(launchctl getenv SSH_AUTH_SOCK)

export FZF_DEFAULT_OPTS="--style full \
  --preview 'fzf-preview.sh {}' \
  --bind 'focus:transform-header:file --brief {}'"
export PATH="$HOME/.local/bin:$PATH"
