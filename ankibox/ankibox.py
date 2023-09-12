#!/usr/bin/env python
#
# ankibox script 2.0
#
# osgav 2023
#

import argparse
import logging
import os

from ankibox.app_config import Config
# from app_config import Config




class VaultIndex:
    '''
    '''

    _index = None

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.vault_root = Config.get_config_item("vault_root")

        VaultIndex._index = []
        for dir, subdir, files in os.walk(self.vault_root):
            for file in files:
                VaultIndex._index.append("{}/{}".format(dir, file))

        self.log.debug("done.")


    @staticmethod
    def get_note_filepath(filename):
        '''
        '''
        if "/" in filename:
            for filepath in VaultIndex._index:
                if filename in filepath:
                    return filepath
        else:
            for filepath in VaultIndex._index:
                if "/{}".format(filename) in filepath:
                    return filepath




class Note:
    '''
    a Note is a markdown file

    a Note is also a markdown file's representation inside an AnkiNote
    
    this class represents that markdown file and all of it's 
    reduced forms, known as "ankinote chunks" or "chunk styles"
    '''
    def __init__(self, title, source=None, **kwargs):
        '''
        the "source" should one of: 
        - "markdown_file"
        - "ankinote"

        anything else is invalid.

        **kwargs should optionally pass in:
        - {'ankinote': details}

        where ankinote 'details' is a dictionary containing:
        - content (the "back of the card")
        - obsidian_to_anki_id (may be present, may be None)
        '''
        self.log = logging.getLogger(self.__class__.__name__)

        self.anki_card_tag = Config.get_config_item("anki_card_tag")

        self.title = title
        self.filename = self.title + ".md"
        self.filepath = self.locate_note()
        
        self.source = source
        
        if self.source == "ankinote":
            self.anki_id = kwargs['ankinote']['obsidian_to_anki_id']
            # this either:
            # - sets self.anki_id to "None"
            # - sets self.anki_id to something like "<!--ID: 1685461928651-->"

        if self.source == "markdown_file":
            self.anki_id = None


    def locate_note(self):
        return VaultIndex.get_note_filepath(self.filename)


    def chunk_style_first_line(self, delete=None):

        from ankibox.chunks import ankinote_chunk_first_line
        from ankibox.chunks import ankinote_chunk_first_line_with_id
        from ankibox.chunks import ankinote_chunk_first_line_delete

        # from chunks import ankinote_chunk_first_line
        # from chunks import ankinote_chunk_first_line_with_id
        # from chunks import ankinote_chunk_first_line_delete

        self.delete = delete

        if self.delete:
            first_line = "note is being removed from ankinote"
        else:
            with open(self.filepath, 'r') as f:
                filelines = f.readlines()
                # now find the first non-blank line
                for line in filelines:
                    # my notes tend to start with a couple of blank lines
                    # which means the first list items after reading the
                    # note with readlines() are newline characters.
                    # so if "\n" is the first list item, keep looking
                    # through the list for some actual text...
                    if line == "\n" or line == "```\n":
                        continue
                    # also, sometimes the first text is "related:" followed
                    # by a bullet list of notes. so if "related:" is found,
                    # then skip ahead to the next item which will be the name
                    # of another note, aka something more interesting.
                    elif line.startswith("related:"):
                        continue
                    else:
                        first_line = line.strip()
                        break

        filepath = self.filepath
        front = self.title
        back = first_line
        tag = self.anki_card_tag

        # which template to use?
        #
        if self.delete:
            template = ankinote_chunk_first_line_delete
            chunk = template.format(
                filepath=filepath,
                anki_card_front=front,
                anki_card_tag=tag,
                anki_card_back=back,
                obsidian_to_anki_id=self.anki_id
            )
            return chunk
        if self.anki_id:
            template = ankinote_chunk_first_line_with_id
            chunk = template.format(
                filepath=filepath,
                anki_card_front=front,
                anki_card_tag=tag,
                anki_card_back=back,
                obsidian_to_anki_id=self.anki_id
            )
            return chunk
        else:
            template = ankinote_chunk_first_line
            chunk = template.format(
                filepath=filepath,
                anki_card_front=front,
                anki_card_tag=tag,
                anki_card_back=back
            )
            return chunk


    def chunk_style_first_heading(self):
        pass




class File:
    '''
    a File is a source of notes for an AnkiBox

    a note with an unknown structure of text inside

    this is a parent class that should be inherited from

    child classes should provide the implementation for
    getting a snapshot of the source of notes
    '''
    def __init__(self, config):
        self.log = logging.getLogger(self.__class__.__name__)
        self.name = config['name']
        self.source_path = config['path']
        self.log.debug("initialized Source (File) for \"{}\"".format(self.name))




class IWQueue(File):
    '''
    an IW Queue is a text file 
    it is edited by the Obsidian plugin "Incremental Writing"

    this class represents that text file
    
    the purpose of this class is to return a list of Note objects
    '''
    def __init__(self, config):
        super().__init__(config)
        self.iw_queue_header_length = 7
        # HARDCODED VALUE... IW queue file headers are 7 lines


    def extract_note_title(self, line):
        '''
        given a line from an IW queue, extract the title of the note
        '''
        line_parts = line.strip().split("|")
        note_title = line_parts[1].strip(" []")
        return note_title


    def get_snapshot(self):
        '''
        a snapshot is a list of Note objects
        '''
        with open(self.source_path, "r") as f:
            filelines = f.readlines()

        item_count = len(filelines) - self.iw_queue_header_length
        self.log.debug("{} items found in \"{}\"".format(item_count, self.name))

        iw_queue_body = filelines[self.iw_queue_header_length:]

        notes = []
        for line in iw_queue_body:
            title = self.extract_note_title(line)
            notes.append(Note(title, source="markdown_file"))
        return notes




class Folder:
    '''
    a Folder is a source of notes for an AnkiBox

    this class represents a directory of markdown files
    '''
    def __init__(self, config):
        self.log = logging.getLogger(self.__class__.__name__)
        self.name = config['name']
        self.source_path = config['path']

        self.log.debug("initialized Source (Folder) for \"{}\"".format(self.name))


    def get_snapshot(self):
        '''
        a snapshot is a list of Note objects
        '''
        md_files = [file for file in os.listdir(self.source_path) if file.endswith('.md')]
        item_count = len(md_files)
        self.log.debug("{} items found in \"{}\"".format(item_count, self.name))

        notes = []
        for file in md_files:
            title = file[:-3] # remove ".md" file extension
            notes.append(Note(title, source="markdown_file"))
        return notes




class AnkiNote:
    '''
    an AnkiNote is a text file
    
    this class represents that text file

    it's purpose is to:
    - create an ankinote file if one doesn't exist
    - write Notes to the ankinote
    - read Notes from the ankinote
    '''
    def __init__(self, config, source_type):
        self.log = logging.getLogger(self.__class__.__name__)

        self.anki_card_tag = Config.get_config_item("anki_card_tag")

        self.name = config['name']
        self.log.debug("initializing AnkiNote for \"{}\"...".format(self.name))
        self.source_path = config['path']
        self.source_type = source_type

        if self.check_for_existing_ankinote():
            pass
        else:
            self.create_ankinote()
        
        self.log.debug("done.")


    def check_for_existing_ankinote(self):

        if self.source_type == "folder":
            # check if folder contains an ankinote in the expected location
            ANKINOTE_FOR_FOLDER = "ankibox/ANKIBOX.md" # HARDCODED VALUE ...
            self.ankinote_path = "{}/{}".format(self.source_path, ANKINOTE_FOR_FOLDER)
            if os.path.isfile(self.ankinote_path):
                self.log.debug("found existing ankinote")
                return True
            else:
                self.log.debug("no existing ankinote found")
                return False

        elif self.source_type == "file":            
            # check if an ankinote exists in the expected location... which is...
            # a "centralised" location for all File-based ankibox ankinotes
            ankinote_storage = Config.get_config_item("file_ankinote_storage")
            self.ankinote_path = "{}/ANKIBOX {}.md".format(ankinote_storage, self.name)
            if os.path.isfile(self.ankinote_path):
                self.log.debug("found existing ankinote")
                return True
            else:
                self.log.debug("no existing ankinote found")
                return False


    def create_ankinote(self):
        self.log.debug("created an AnkiNote for \"{}\" (NOT REALLY THOUGH)".format(self.name))
        # TODO: add a debug print log, one that says "created ankinote: /path/goes/here/or/something"


    def get_snapshot(self):
        '''
        a snapshot is a list of Note objects
        '''

        if os.path.isfile(self.ankinote_path):
            pass
        else:
            self.log.debug("can't snapshot a file that doesn't exist yet!")
            return []
        
        with open(self.ankinote_path, "r") as f:
            filelines = f.readlines()
        
        if len(filelines) == 0:
            self.log.debug("the ankinote is empty!")
            return []

        notes = []
        with open(self.ankinote_path, "r") as f:
            filestring = f.read()
        ankinote_entries = filestring.split("---\n")

        ankinote_entries = ankinote_entries[1:-1]
        # [1:-1] list slice is to cut off the first and last items
        # the first is the ANKINOTE_HEADER section
        # the last is a couple of blank lines after the final --- divider
        
        self.log.debug("{} items found in \"{}\"".format(len(ankinote_entries), self.name))

        for entry in ankinote_entries:

            details = {}
            details['filepath'] = self.extract_filepath_from_ankinote_entry(entry)
            details['filename'] = self.extract_filename_from_filepath(details['filepath'])
            details['card_front'] = self.extract_card_front_from_ankinote_entry(entry)
            details['card_back'] = self.extract_card_back_from_ankinote_entry(entry)
            details['obsidian_to_anki_id'] = self.extract_obsidian_to_anki_id_from_ankinote_entry(entry)

            title = details['card_front']
            ankinote_entry = {'ankinote': details}
            notes.append(Note(title, source="ankinote", **ankinote_entry))

        return notes

    def extract_filepath_from_ankinote_entry(self, entry):
        entry_lines = entry.split("\n")
        for line in entry_lines:
            if line.startswith("filepath:"):
                return line.split(":")[1].strip()

    def extract_filename_from_filepath(self, path):
        return path.split("/")[-1]

    def extract_card_front_from_ankinote_entry(self, entry):
        entry_lines = entry.split("\n")
        for line in entry_lines:
            if line.endswith(self.anki_card_tag):
                return line.removesuffix(self.anki_card_tag).strip()

    def extract_card_back_from_ankinote_entry(self, entry):
        entry_lines = entry.split("\n")
        card_front_index = None
        for index, line in enumerate(entry_lines):
            if line.endswith(self.anki_card_tag):
                card_front_index = index
                break
        return entry_lines[card_front_index + 1]

    def extract_obsidian_to_anki_id_from_ankinote_entry(self, entry):
        entry_lines = entry.split("\n")
        for line in entry_lines:
            if line.startswith("<!--ID:"):
                return line.strip()


    def write_chunks_to_ankinote(self, chunks):
        self.log.debug("writing chunks to ankinote...")
        #
        # this is a relatively dumb function
        # it receives a list of strings and writes them to a file
        # the only special thing it does is write one particular 
        # string to that file first
        #

        from ankibox.chunks import ankinote_chunk_header
        # from chunks import ankinote_chunk_header

        with open (self.ankinote_path, "w") as f:
            f.write(ankinote_chunk_header.format(ankibox_name=self.name))
            for chunk in chunks:
                f.write(chunk)
        
        self.log.debug("done.")





class AnkiBox:
    '''
    an AnkiBox is an abstract concept
    
    it is the idea of taking a source of notes and synchronizing
    them with a deck in anki

    it is the tying together of:
    - a source of notes (based on a Folder or a File)
    - a deck in anki (interfaced with via Obsidian_to_Anki obsidian plugin)
    - a special text file for synchronising those two things (an AnkiNote)
    - a name to refer to the specific ankibox

    an "AnkiBox" synchronizes a "Source" of notes with an "AnkiNote"

    a "Source" is either a "Folder" or a "File"

    a "File" may be an "IWQueue" or some other format
    '''        
    def __init__(self, name, action, ankinote: AnkiNote, source):
        self.log = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.log.debug("initializing AnkiBox for \"{}\"".format(self.name))
        self.action = action
        self.ankinote = ankinote
        self.source = source
        self.log.debug("done.")

        self.log.debug("processing command line arguments...")

        if self.action.add and self.action.delete:
            self.log.warning("add+delete at the same time: not implemented")
        
        elif self.action.add:
            self.add_new_notes()
        
        elif self.action.delete:
            self.remove_old_notes()
        
        elif self.action.summary:
            self.summary_short()
        
        else:
            self.summary_long()
            



    def get_state(self):
        '''
        compiles a dict containing item counts, note titles, and lists of Notes.
        collectively that represents the current state of the AnkiBox...
        '''
        self.log.debug("determining AnkiBox state...")

        snapshot_source = self.source.get_snapshot() ## ahh these are white instead of orange now with the new AnkiBox.init method...
        snapshot_ankinote = self.ankinote.get_snapshot() ## ahh if i specify the type in the constructor then it's orange again...

        count_source_total = len(snapshot_source)
        count_ankinote_total = len(snapshot_ankinote)

        titles_source_all = []
        titles_ankinote_all = []

        for note in snapshot_source:
            titles_source_all.append(note.title)
        for note in snapshot_ankinote:
            titles_ankinote_all.append(note.title)

        notes_source_new = []
        notes_ankinote_old = []

        for note in snapshot_source:
            if note.title in titles_ankinote_all:
                continue
            else:
                notes_source_new.append(note)
        for note in snapshot_ankinote:
            if note.title in titles_source_all:
                continue
            else:
                notes_ankinote_old.append(note)
        
        count_source_new = len(notes_source_new)
        count_ankinote_old = len(notes_ankinote_old)

        titles_source_new = []
        titles_ankinote_old = []

        for note in notes_source_new:
            titles_source_new.append(note.title)
        for note in notes_ankinote_old:
            titles_ankinote_old.append(note.title)
        
        count_ankinote_anki_ids = 0
        for note in snapshot_ankinote:
            if note.anki_id:
                count_ankinote_anki_ids += 1
            else:
                continue

        ankibox_state = {}
        # ankibox_state['snapshot_source'] = snapshot_source
        ankibox_state['snapshot_ankinote'] = snapshot_ankinote                      # add, remove
        ankibox_state['count_source_total'] = count_source_total                    # summary
        ankibox_state['count_ankinote_total'] = count_ankinote_total                # summary
        ankibox_state['titles_source_all'] = titles_source_all                      # remove
        # ankibox_state['titles_ankinote_all'] = titles_ankinote_all
        ankibox_state['count_source_new'] = count_source_new                        # summary, add
        ankibox_state['count_ankinote_old'] = count_ankinote_old                    # summary, remove
        ankibox_state['titles_source_new'] = titles_source_new                      # summary
        ankibox_state['titles_ankinote_old'] = titles_ankinote_old                  # summary
        ankibox_state['notes_source_new'] = notes_source_new                        # add
        # ankibox_state['notes_ankinote_old'] = notes_ankinote_old
        ankibox_state['count_ankinote_anki_ids'] = count_ankinote_anki_ids          # summary

        self.log.debug("done.")

        return ankibox_state


    def summary_short(self):
        '''
        print summary of ankibox state (new / old numbers only)
        '''
        self.log.debug("printing summary (new shorter version of short")
        state = self.get_state()
        count_source_new = state['count_source_new']
        count_ankinote_old = state['count_ankinote_old']

        clrz = {}
        clrz['GREEN'] = '\033[92m'
        clrz['YELLOW'] = '\033[93m'
        clrz['ENDC'] = '\033[0m'
        clrz['BOLD'] = '\033[1m'

        if count_source_new > 0:
            string_for_new = "{}{}{} new{}".format(
                                                   clrz['BOLD'],
                                                   clrz['GREEN'],
                                                   count_source_new,
                                                   clrz['ENDC']
                                                   )
        else:
            string_for_new = "{} new".format(count_source_new)

        if count_ankinote_old > 0:
            string_for_old = "{}{}{} old{}".format(
                                                   clrz['BOLD'],
                                                   clrz['YELLOW'],
                                                   count_ankinote_old,
                                                   clrz['ENDC']
                                                   )
        else:
            string_for_old = "{} old".format(count_ankinote_old)

        print("{}\t {}\t  {}".format(
                                            string_for_new,
                                            string_for_old,
                                            self.name
                                            )
        )


    def print_divider(self, name):
        dash_multiplier = 80 - 6 - len(name)
        dashes = "-" * dash_multiplier
        print("\n---> {} {}".format(name, dashes))


    def summary_long(self):
        '''
        print summary of ankibox state (numbers and note titles)
        '''
        self.log.debug("printing summary (long)")
        self.print_divider(self.name)
        state = self.get_state()
        count_source_new = state['count_source_new']
        count_ankinote_old = state['count_ankinote_old']
        count_source_total = state['count_source_total']
        count_ankinote_total = state['count_ankinote_total']
        count_ankinote_anki_ids = state['count_ankinote_anki_ids']
        titles_source_new = state['titles_source_new']
        titles_ankinote_old = state['titles_ankinote_old']
        print("")
        print("{} new notes found in \"{}\" source".format(count_source_new, self.name))
        print("{} old notes found in \"{}\" ankinote".format(count_ankinote_old, self.name))
        print("")
        print("{} notes found in \"{}\" source".format(count_source_total, self.name))
        print("{} notes found in \"{}\" ankinote".format(count_ankinote_total, self.name))


        #
        # make this next bit conditional? i.e. only show it when it represents an "unfinished add operation"
        # this should make it more obvious there is an unfinished add operation, as the output will be
        # different, i.e. longer and showing the count of unadded notes...
        # well, this bit would show it by not being the same count as count_ankinote_total
        # but another count could be added above after the "old notes" count
        # this would more closely match the OG ankibox output
        #
        print("{} notes found in \"{}\" ankinote w/ID".format(count_ankinote_anki_ids, self.name))
        print("")
        #
        # to be fair the bit below, ending with "ankibox is in-sync" could do with factoring in
        # the anki IDs... currently it's possible to have an "unfinished add operation" and have
        # the script say the ankibox is in-sync. it's only *half* in-sync if there is an unfinished
        # add operation lingering...
        #
        #

        if count_source_new + count_ankinote_old > 0:
            if count_source_new > 0:
                print("new notes in source:")
                for note in titles_source_new:
                    print("- {}".format(note))
            if count_ankinote_old > 0:
                print("old notes in ankinote:")
                for note in titles_ankinote_old:
                    print("- {}".format(note))
            print("")
        else:
            print("\"{}\" is in-sync.".format(self.name))



    def add_new_notes(self):
        '''
        the add operation
        '''
        self.log.debug("starting add operation")
        self.summary_long()

        # step 1: get ankibox state
        state = self.get_state()
        ankinote_snapshot = state['snapshot_ankinote']
        notes_source_new = state['notes_source_new']
        count_source_new = state['count_source_new']

        # step 2: check for new notes to add
        self.log.debug("checking source for new notes...")
        if count_source_new:
            self.log.debug("there are new notes to be added.")
        else:
            self.log.debug("no new notes to add.")
            self.log.debug("no action taken.")
            print("no new notes to add.")
            print("no action taken.")
            return

        # step 3: compile chunks for ankinote
        chunks = []
        for note in notes_source_new:
            # gather the new notes in the source...
            chunks.append(note.chunk_style_first_line())
        for note in ankinote_snapshot:
            # ...and all the existing notes in the ankinote.
            chunks.append(note.chunk_style_first_line())

        # step 4: write the ankinote
        self.ankinote.write_chunks_to_ankinote(chunks)

        # step 5: prompt the user to run the Obsidian_to_Anki plugin
        self.action_required_prompt("add operation completed, go run Obsidian_to_Anki plugin!")

        # boom, add operation is done
        print("added {} new notes.".format(count_source_new))
        print("add operation completed.")

    
    def remove_old_notes(self):
        '''
        the delete operation
        '''
        self.log.debug("starting delete operation")
        self.summary_long()

        # step 1: get ankibox state
        state = self.get_state()
        ankinote_snapshot = state['snapshot_ankinote']
        titles_source_all = state['titles_source_all']
        count_ankinote_old = state['count_ankinote_old']
        
        # step 2: check for old notes to delete
        self.log.debug("checking ankinote for old notes...")
        if count_ankinote_old:
            self.log.debug("there are old notes to be deleted.")
            # notes_ankinote_old = state['notes_ankinote_old']
        else:
            self.log.debug("no old notes to delete.")
            self.log.debug("no action taken.")
            print("no old notes to delete.")
            print("no action taken.")
            return

        # step 3: check for unfinished add operation
        self.log.debug("checking ankinote for unadded entries...")
        unadded_entries = 0
        for note in ankinote_snapshot:
            if note.anki_id:
                continue
            else:
                unadded_entries +=1
                self.log.debug("unadded note: {}".format(note.title))
        
        if unadded_entries:
            self.log.debug("found {} notes in ankinote without an ID".format(unadded_entries))
            self.log.debug("cannot continue, finish add operation first by running Obsidian_to_Anki plugin!")
            print("found {} notes in ankinote without an ID".format(unadded_entries))
            print("cannot continue, finish add operation first by running Obsidian_to_Anki plugin!")
            return

        # step 4: identify which notes will remain in the ankinote
        self.log.debug("marking ankinote entries that were found in the source...")
        for note in ankinote_snapshot:
            if note.title in titles_source_all:
                note.found_in_source = True
        
        # step 5: compile chunks for first ankinote: 
        #         the intermediary one containing "DELETE" statements
        self.log.debug("compiling chunks for intermediary ankinote...")
        chunks_intermediary = []
        for note in ankinote_snapshot:
            try:
                if note.found_in_source:
                    # note found in source, so write it into ankinote like it was before
                    chunks_intermediary.append(note.chunk_style_first_line())
            except AttributeError:
                # note was NOT found in source, so write it into ankinote using a "DELETE" chunk
                chunks_intermediary.append(note.chunk_style_first_line(delete=True))
        
        # step 6: write the intermediary ankinote
        self.log.debug("writing intermediary ankinote...")
        self.ankinote.write_chunks_to_ankinote(chunks_intermediary)

        # step 7: prompt the user to run the Obsidian_to_Anki plugin
        self.log.debug("pausing script for user to take external action...")
        message = "run the Obsidian_to_Anki plugin to perform DELETEs before continuing!"
        self.action_required_prompt(message, are_you_sure=True)
        
        # step 8: compile chunks for second ankinote: 
        #         the final one with old notes removed
        self.log.debug("compiling chunks for final ankinote...")
        chunks_final = []
        for note in ankinote_snapshot:
            try:
                if note.found_in_source:
                    chunks_final.append(note.chunk_style_first_line())
            except AttributeError:
                continue

        # step 9: write the final ankinote
        self.log.debug("writing final ankinote...")
        self.ankinote.write_chunks_to_ankinote(chunks_final)

        # boom, delete operation is done
        print("removed {} old notes.".format(count_ankinote_old))
        print("delete operation completed.")
        


    def action_required_prompt(self, message, are_you_sure=False):
        '''
        pause the script by prompting for user input, to create
        a window of time in which the user can run the required
        external process (the Obsidian_to_Anki plugin)
        '''
        print("\n[ACTION REQUIRED] {}".format(message))
        if are_you_sure:
            input("\npress <ENTER> to continue...")
            input("press <ENTER> again to confirm you really are ready...")
            input("you have DEFINITELY run the Obsidian_to_Anki plugin and are ready to proceed?")
            input("ok then, press <ENTER> to continue...\n")
        else:
            input("\npress <ENTER> to continue...\n")


class App:
    def __init__(self, cli_args):

        logging.basicConfig(
            level=logging.INFO,
            # format='[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s] %(message)s',
            format='[%(levelname)s] [%(name)s.%(funcName)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
            )
        self.log = logging.getLogger(self.__class__.__name__)

        self.log.debug("reading command line arguments...")
        self.cli = cli_args
        if self.cli.summary:
            print("")

        self.log.debug("loading config file...")
        Config(self.cli)

        self.log.debug("initializing VaultIndex...")
        VaultIndex()


    def run(self):

        # still splitting up folders and files from the config
        source_folders = []
        for config in Config.get_config_item("folder"):
            source_folders.append(config)
        source_files = []
        for config in Config.get_config_item("file"):
            source_files.append(config)
        
        for folder in source_folders:
            name = folder['name']
            self.log.debug("initializing \"{}\"".format(name))
            action = self.cli
            source = Folder(folder)
            ankinote = AnkiNote(folder, "folder")
            ankibox = AnkiBox(name, action, ankinote, source)

        for file in source_files:
            name = file['name']
            self.log.debug("initializing \"{}\"".format(name))
            action = self.cli
            source = IWQueue(file)
            # 'source' should be set via some logic that figures
            # out which "source of notes" class is appropriate
            # based on file['type']
            ankinote = AnkiNote(file, "file")
            ankibox = AnkiBox(name, action, ankinote, source)

        self.log.debug("done.")
        print("")
        print("")




def main():

    parser = argparse.ArgumentParser(description="ankibox: turn notes into anki cards")
    parser.add_argument(
        '-a',
        '--add',
        action='store_true',
        dest='add',
        help='add new notes to ankibox'
    )
    parser.add_argument(
        '-d',
        '--delete',
        action='store_true',
        dest='delete',
        help='remove processed notes from ankibox'
    )
    parser.add_argument(
        '-s',
        '--summary',
        action='store_true',
        dest='summary',
        help='print short summary of ankibox status'
    )
    parser.add_argument(
        '-c',
        '--config',
        action='store_true',
        dest='config',
        help='specify config file location (this option is not configured correctly yet)'
        # TESTING.. see the Config class
    )
    args = parser.parse_args()

    app = App(args)
    app.run()




if __name__ == '__main__':
    main()

