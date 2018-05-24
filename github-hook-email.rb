#! /usr/bin/env ruby

require 'json'
require 'date'

def align(text, indent = '  ')
  margin = text[/\A\s+/].size

  text.gsub(/^\s{#{margin}}/, indent)
end

def commits
  Array($payload['commits'])
end

def shorten(text, limit)
  text.slice(0, limit) << '...'
end

def name_with_owner
  File.join(owner_name, repository_name)
end

def owner_name
  $payload['repository']['owner']['login']
end

def repository_name
  $payload['repository']['name']
end

def repo_url
  $payload['repository']['url']
end

# Public
def mail_subject
  if first_commit
    "[#{name_with_owner}] #{first_commit_sha.slice(0, 6)}: #{first_commit_title}"
  else
    "[#{name_with_owner}]"
  end
end

# Public
def mail_body
  body = commits.inject(repository_text) do |text, commit|
    text << commit_text(commit)
  end

  body << compare_text unless single_commit?

  body
end

def repository_text
  align(<<-EOH)
        Branch: #{branch_ref}
        Home:   #{repo_url}
      EOH
end

def commit_text(commit)
  gitsha   = commit['id']
  added    = commit['added'].map    { |f| ['A', f] }
  removed  = commit['removed'].map  { |f| ['R', f] }
  modified = commit['modified'].map { |f| ['M', f] }

  changed_paths = (added + removed + modified).sort_by { |(char, file)| file }
  changed_paths = changed_paths.collect { |entry| entry * ' ' }.join("\n    ")

  timestamp = Date.parse(commit['timestamp'])

  commit_author = "#{commit['author']['name']} <#{commit['author']['email']}>"

  text = align(<<-EOH)
        Commit: #{gitsha}
            #{commit['url']}
        Author: #{commit_author}
        Date:   #{timestamp} (#{timestamp.strftime('%a, %d %b %Y')})

      EOH

  if changed_paths.size > 0
    text << align(<<-EOH)
          Changed paths:
            #{changed_paths}

        EOH
  end

  text << align(<<-EOH)
        Log Message:
        -----------
        #{commit['message']}


      EOH

  text
end

def compare_text
  "Compare: #{$payload['compare']}"
end

def single_commit?
  first_commit == last_commit
end

def branch_ref
  $payload['ref']
end

def author_address
  "#{author_name} <#{author_email}>"
end

def author
  commit = last_commit || {}
  commit['author'] || commit['committer'] || $payload['pusher']
end

def author_name
  author['name']
end

def author_email
  author['email']
end

def last_commit
  $payload['commits'].last # assume that the last committer is also the pusher
end

def first_commit_sha
  first_commit['id']
end

def first_commit_title(limit = 50)
  title_line = first_commit['message'][/\A[^\n]+/] || ''

  title_line.length > limit ? shorten(title_line, limit) : title_line
end

def first_commit
  $payload['commits'].first
end

# must be a difference with push $payloads
def owner_name
  $payload['repository']['owner']['name']
end

## main
$payload = JSON.parse(ARGV[0])
puts mail_subject
puts mail_body
